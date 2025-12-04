from flask import Flask, request, jsonify, send_from_directory
import pymysql
import os

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_url_path='')
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')

# DB Configuration
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/settlements')
def get_settlements():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({'error': 'start_date and end_date are required'}), 400

    query = """
        select 
            T3.id                                   as manager_id,
            T3.name                                 as name,
            sum(T1.settlement_amount)               as total_amount,
            COALESCE(sum(T5.price), 0)              as total_tip
        from manager_settlement T1
                left join `match` T2 on T1.match_id = T2.id
                left join manager T3 on T2.manager_id = T3.id
                left join auth_user T4 on T3.user_id = T4.id
                left join manager_tip T5 on T2.id = T5.match_id and T3.id = T5.manager_id
        where T4.is_staff = 1
        and T3.is_open = 1
        and T3.name != "매니저팀"
        and date(convert_tz(T2.schedule, 'UTC', 'Asia/Seoul')) >= %s
        and date(convert_tz(T2.schedule, 'UTC', 'Asia/Seoul')) <= %s
        and T2.status = "RELEASE"
        group by T3.id, T3.name
        order by T3.name;
    """

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(query, (start_date, end_date))
            results = cursor.fetchall()
        conn.close()
        
        # Ensure decimals are converted to float/int for JSON serialization if needed
        # PyMySQL returns Decimal for money types usually
        for row in results:
            if row['total_amount']:
                row['total_amount'] = float(row['total_amount'])
            else:
                row['total_amount'] = 0
            
            if row['total_tip']:
                row['total_tip'] = float(row['total_tip'])
            else:
                row['total_tip'] = 0

        return jsonify(results)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/manager/<int:manager_id>/matches')
def get_manager_matches(manager_id):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({'error': 'start_date and end_date are required'}), 400

    query = """
        select 
            T2.id as match_id,
            date(convert_tz(T2.schedule, 'UTC', 'Asia/Seoul')) as match_date,
            time(convert_tz(T2.schedule, 'UTC', 'Asia/Seoul')) as match_time,
            T1.settlement_amount as settlement_amount,
            COALESCE(T5.price, 0) as tip_amount,
            T2.match_title as match_title,
            T7.name as stadium_name,
            T8.name as stadium_group_name,
            T2.max_player_cnt as max_player_cnt,
            T2.type as match_type
        from manager_settlement T1
                left join `match` T2 on T1.match_id = T2.id
                left join manager T3 on T2.manager_id = T3.id
                left join auth_user T4 on T3.user_id = T4.id
                left join manager_tip T5 on T2.id = T5.match_id and T3.id = T5.manager_id
                left join stadium T7 on T2.stadium_id = T7.id
                left join stadium_group T8 on T7.group_id = T8.id
        where T4.is_staff = 1
        and T3.is_open = 1
        and T3.id = %s
        and T3.name != "매니저팀"
        and date(convert_tz(T2.schedule, 'UTC', 'Asia/Seoul')) >= %s
        and date(convert_tz(T2.schedule, 'UTC', 'Asia/Seoul')) <= %s
        and T2.status = "RELEASE"
        order by T2.schedule asc;
    """

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(query, (manager_id, start_date, end_date))
            results = cursor.fetchall()
        conn.close()
        
        for row in results:
            if row['settlement_amount']:
                row['settlement_amount'] = float(row['settlement_amount'])
            else:
                row['settlement_amount'] = 0
            
            if row['tip_amount']:
                row['tip_amount'] = float(row['tip_amount'])
            else:
                row['tip_amount'] = 0
            
            # Convert date to string
            if row['match_date']:
                row['match_date'] = row['match_date'].strftime('%Y-%m-%d')
            
            # Convert time to string
            if row['match_time']:
                row['match_time'] = str(row['match_time'])
            
            # Construct match title if null
            if not row['match_title']:
                stadium_text = f"{row['stadium_group_name']} {row['stadium_name']}"
                
                # Player count format (e.g., 11vs11)
                player_cnt = row['max_player_cnt']
                vs_format = ""
                if player_cnt:
                    half_cnt = int(player_cnt / 2)
                    vs_format = f"{half_cnt}vs{half_cnt}"
                
                # Match type format
                type_map = {
                    'match': '축구 매치',
                    '3teams': '3파전',
                    'starter': '스타터 매치',
                    'cup': '컵',
                    'league': '리그',
                    'tshirt': '티셔츠'
                }
                type_text = type_map.get(row['match_type'], '매치')
                
                # Combine them
                parts = [stadium_text]
                if vs_format:
                    parts.append(vs_format)
                parts.append(type_text)
                
                row['match_title'] = " ".join(parts)
            
            # Use match_title as the stadium_name to be displayed
            row['stadium_name'] = row['match_title']

        return jsonify(results)
    except Exception as e:
        print(f"Error in get_manager_matches: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/stadium-columns')
def debug_stadium_columns():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SHOW COLUMNS FROM stadium")
            columns = cursor.fetchall()
        conn.close()
        return jsonify(columns)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/stadium-data')
def debug_stadium_data():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM stadium LIMIT 5")
            data = cursor.fetchall()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/match-stadium')
def debug_match_stadium():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    T2.id as match_id,
                    T2.stadium_id,
                    T7.title as stadium_title,
                    T7.name as stadium_name
                FROM `match` T2
                LEFT JOIN stadium T7 ON T2.stadium_id = T7.id
                WHERE T2.status = 'RELEASE'
                LIMIT 10
            """)
            data = cursor.fetchall()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/match-type')
def debug_match_type():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    T2.id as match_id,
                    T2.type,
                    T2.match_type_id,
                    T9.name as match_type_name
                FROM `match` T2
                LEFT JOIN match_type T9 ON T2.match_type_id = T9.id
                WHERE T2.status = 'RELEASE'
                LIMIT 10
            """)
            data = cursor.fetchall()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/match/<int:match_id>')
def debug_match_detail(match_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM `match` WHERE id = %s", (match_id,))
            data = cursor.fetchone()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/matches-by-date')
def debug_matches_by_date():
    date = request.args.get('date') # YYYY-MM-DD
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, match_title, schedule, stadium_id, type 
                FROM `match` 
                WHERE date(convert_tz(schedule, 'UTC', 'Asia/Seoul')) = %s
            """, (date,))
            data = cursor.fetchall()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    
    if os.getenv('FLASK_ENV') == 'development':
        print("Starting Flask server (Development)...")
        print(f"Open http://localhost:{port} in your browser.")
        app.run(host='0.0.0.0', debug=True, port=port)
    else:
        from waitress import serve
        print("Starting Production Server (Waitress)...")
        print(f"Server running on port {port}")
        serve(app, host='0.0.0.0', port=port)

