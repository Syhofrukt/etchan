function showSection(section) {
            const sections = document.querySelectorAll('.leaderboard-section');
            const buttons = document.querySelectorAll('.section-button');

            sections.forEach(s => s.classList.remove('active'));
            buttons.forEach(b => b.classList.remove('active'));

            document.getElementById('section-' + section).classList.add('active');
            event.target.classList.add('active');
        }