# Manager Settlement Dashboard

매니저 정산 대시보드 - 매니저별 정산 금액 및 팁을 조회하는 웹 애플리케이션

## 🎯 주요 기능

- 📅 기간별 매니저 정산 금액 조회
- 💰 매니저별 팁 금액 확인
- 📊 매치별 상세 내역 확인
- 🏟️ 구장 정보 및 매치 타입 표시
- 👥 최대 인원 정보 표시

## 🚀 빠른 시작

### 로컬 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 데이터베이스 정보 입력

# 서버 실행
python app.py
```

개발 모드: http://localhost:8080

### Render 배포

자세한 배포 가이드는 [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)를 참고하세요.

## 📋 요구사항

- Python 3.11+
- MySQL 데이터베이스 접근 권한

## 🔧 기술 스택

- **Backend**: Flask
- **Database**: MySQL (PyMySQL)
- **Frontend**: HTML, CSS (Tailwind), JavaScript
- **Production Server**: Waitress / Gunicorn

## 📁 프로젝트 구조

```
manager-settlement-dashboard/
├── app.py                      # Flask 애플리케이션
├── requirements.txt            # Python 의존성
├── runtime.txt                 # Python 버전
├── Procfile                    # Render 배포 설정
├── .env.example                # 환경 변수 템플릿
├── .gitignore                  # Git 제외 파일
├── static/
│   ├── index.html             # 메인 페이지
│   └── script.js              # 프론트엔드 로직
├── RENDER_DEPLOYMENT.md       # Render 배포 가이드
└── README.md                  # 이 파일
```

## 🔐 환경 변수

`.env` 파일에 다음 변수들을 설정하세요:

```
DB_HOST=your-database-host
DB_USER=your-database-user
DB_PASS=your-database-password
DB_NAME=plab
FLASK_ENV=production
SECRET_KEY=your-secret-key
```

## 📝 라이선스

Private - 내부 사용 전용

## 👥 개발자

Plab Team

---

**마지막 업데이트**: 2025-12-02
