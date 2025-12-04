document.addEventListener('DOMContentLoaded', () => {
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    const searchBtn = document.getElementById('searchBtn');
    const sqlPreview = document.getElementById('sqlPreview');
    const copySqlBtn = document.getElementById('copySqlBtn');
    const resultBody = document.getElementById('resultBody');
    const resultCount = document.getElementById('resultCount');
    const totalSumEl = document.getElementById('totalSum');
    const totalTipEl = document.getElementById('totalTip');

    // Default dates (Start of current month to today)
    const today = new Date();
    const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);

    startDateInput.valueAsDate = startOfMonth;
    endDateInput.valueAsDate = today;

    // Base SQL Template
    const baseQuery = `select 
    T3.id                                   as "매니저 ID",
    T3.name                                 as "이름",
    sum(T1.settlement_amount)               as "정산 금액 합계"
from manager_settlement T1
         left join \`match\` T2 on T1.match_id = T2.id
         left join manager T3 on T2.manager_id = T3.id
         left join auth_user T4 on T3.user_id = T4.id
where T4.is_staff = 1
  and T3.is_open = 1
  and date(convert_tz(T2.schedule, 'UTC', 'Asia/Seoul')) >= "{{start_date}}"
  and date(convert_tz(T2.schedule, 'UTC', 'Asia/Seoul')) <= "{{end_date}}"
  and T2.status = "RELEASE"
group by T3.id, T3.name
order by T3.name;`;

    function formatCurrency(amount) {
        return new Intl.NumberFormat('ko-KR').format(amount);
    }

    async function updateDashboard() {
        const start = startDateInput.value;
        const end = endDateInput.value;

        if (!start || !end) {
            alert('시작 날짜와 종료 날짜를 모두 선택해주세요.');
            return;
        }

        // 1. Update SQL Preview
        const query = baseQuery
            .replace('{{start_date}}', start)
            .replace('{{end_date}}', end);

        sqlPreview.textContent = query;

        // 2. Fetch Data from API
        resultBody.innerHTML = `<tr><td colspan="4" class="px-6 py-8 text-center text-gray-500">데이터를 불러오는 중...</td></tr>`;

        try {
            const response = await fetch(`/api/settlements?start_date=${start}&end_date=${end}`);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            renderTable(data);
        } catch (error) {
            console.error('Error:', error);
            resultBody.innerHTML = `<tr><td colspan="4" class="px-6 py-8 text-center text-red-500">오류가 발생했습니다: ${error.message}</td></tr>`;
        }
    }

    function renderTable(data) {
        resultBody.innerHTML = '';
        let total = 0;
        let totalTip = 0;

        if (data.length === 0) {
            resultBody.innerHTML = `<tr><td colspan="4" class="px-6 py-8 text-center text-gray-500">데이터가 없습니다.</td></tr>`;
            resultCount.textContent = `0건 조회됨`;
            totalSumEl.textContent = '-';
            totalTipEl.textContent = '-';
            return;
        }

        data.forEach(row => {
            const amount = row.total_amount || 0;
            const tip = row.total_tip || 0;
            total += amount;
            totalTip += tip;
            const tr = document.createElement('tr');
            tr.className = 'hover:bg-gray-50 transition-colors';
            tr.dataset.managerId = row.manager_id;
            tr.dataset.managerName = row.name;
            tr.innerHTML = `
                <td class="px-6 py-4 text-gray-900 font-medium">${row.manager_id}</td>
                <td class="px-6 py-4 text-gray-700">
                    <button class="text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1 manager-name-btn">
                        <i data-lucide="chevron-right" class="w-4 h-4 transition-transform expand-icon"></i>
                        ${row.name}
                    </button>
                </td>
                <td class="px-6 py-4 text-right text-gray-900 font-medium">${formatCurrency(amount)}</td>
                <td class="px-6 py-4 text-right text-green-600 font-medium">${formatCurrency(tip)}</td>
            `;

            // Add click handler for expansion
            const nameBtn = tr.querySelector('.manager-name-btn');
            nameBtn.addEventListener('click', () => toggleMatchDetails(tr, row.manager_id, row.name));

            resultBody.appendChild(tr);
        });

        resultCount.textContent = `${data.length}건 조회됨`;
        totalSumEl.textContent = formatCurrency(total);
        totalTipEl.textContent = formatCurrency(totalTip);

        // Re-render icons
        lucide.createIcons();
    }

    async function toggleMatchDetails(row, managerId, managerName) {
        const existingDetails = row.nextElementSibling;
        const expandIcon = row.querySelector('.expand-icon');

        // If already expanded, collapse it
        if (existingDetails && existingDetails.classList.contains('match-details-row')) {
            existingDetails.remove();
            expandIcon.style.transform = 'rotate(0deg)';
            return;
        }

        // Expand: rotate icon
        expandIcon.style.transform = 'rotate(90deg)';

        // Create details row
        const detailsRow = document.createElement('tr');
        detailsRow.className = 'match-details-row bg-gray-50';
        detailsRow.innerHTML = `
            <td colspan="4" class="px-6 py-4">
                <div class="bg-white rounded-lg border border-gray-200 p-4">
                    <h3 class="font-semibold text-gray-900 mb-3">${managerName}님의 매치 내역</h3>
                    <div class="match-details-content">
                        <p class="text-gray-500 text-sm">로딩 중...</p>
                    </div>
                </div>
            </td>
        `;

        row.after(detailsRow);

        // Fetch match details
        try {
            const start = startDateInput.value;
            const end = endDateInput.value;
            const response = await fetch(`/api/manager/${managerId}/matches?start_date=${start}&end_date=${end}`);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to fetch match details');
            }

            const matches = await response.json();
            const contentDiv = detailsRow.querySelector('.match-details-content');

            if (matches.length === 0) {
                contentDiv.innerHTML = '<p class="text-gray-500 text-sm">매치 내역이 없습니다.</p>';
                return;
            }

            // Render matches table
            let matchesHTML = `
                <table class="w-full text-sm">
                    <thead class="bg-gray-50 text-gray-600 border-b border-gray-200">
                        <tr>
                            <th class="px-4 py-2 text-left">매치 ID</th>
                            <th class="px-4 py-2 text-left">날짜</th>
                            <th class="px-4 py-2 text-left">구장</th>
                            <th class="px-4 py-2 text-center">최대 인원</th>
                            <th class="px-4 py-2 text-right">정산 금액</th>
                            <th class="px-4 py-2 text-right">팁 금액</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100">
            `;

            matches.forEach(match => {
                matchesHTML += `
                    <tr class="hover:bg-gray-50">
                        <td class="px-4 py-2 text-gray-600">${match.match_id}</td>
                        <td class="px-4 py-2 text-gray-600">${match.match_date}</td>
                        <td class="px-4 py-2 text-gray-600">${match.stadium_name || '-'}</td>
                        <td class="px-4 py-2 text-center text-gray-600">${match.max_player_cnt || '-'}명</td>
                        <td class="px-4 py-2 text-right text-gray-900 font-medium">${formatCurrency(match.settlement_amount)}</td>
                        <td class="px-4 py-2 text-right text-green-600 font-medium">${formatCurrency(match.tip_amount)}</td>
                    </tr>
                `;
            });

            matchesHTML += `
                    </tbody>
                </table>
            `;

            contentDiv.innerHTML = matchesHTML;

        } catch (error) {
            console.error('Error fetching match details:', error);
            const contentDiv = detailsRow.querySelector('.match-details-content');
            contentDiv.innerHTML = `<p class="text-red-500 text-sm">매치 내역을 불러오는데 실패했습니다: ${error.message}</p>`;
        }
    }

    // Event Listeners
    searchBtn.addEventListener('click', updateDashboard);

    copySqlBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(sqlPreview.textContent).then(() => {
            const originalText = copySqlBtn.innerHTML;
            copySqlBtn.innerHTML = `<i data-lucide="check" class="w-3 h-3"></i> 복사됨`;
            setTimeout(() => {
                copySqlBtn.innerHTML = originalText;
                lucide.createIcons();
            }, 2000);
            lucide.createIcons();
        });
    });

    // SQL Toggle
    const sqlToggleHeader = document.getElementById('sqlToggleHeader');
    const sqlContent = document.getElementById('sqlContent');
    const sqlToggleIcon = document.getElementById('sqlToggleIcon');

    sqlToggleHeader.addEventListener('click', () => {
        sqlContent.classList.toggle('hidden');
        sqlToggleIcon.style.transform = sqlContent.classList.contains('hidden')
            ? 'rotate(0deg)'
            : 'rotate(90deg)';
    });

    // Initial Load
    updateDashboard();
});
