import re

with open("templates/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Replace the closing script tag content with full logic.
html = html.split('<script>')[0]

NEW_JS = """
<!-- Login Overlay -->
<div id="login-overlay" style="position:fixed; top:0; left:0; width:100%; height:100%; background:var(--bg); z-index:9999; display:flex; justify-content:center; align-items:center;">
    <div style="background:var(--surface); padding:40px; border:1px solid var(--border); border-radius:4px; width:340px;">
        <div class="logo-monogram" style="text-align:center; font-size:36px; margin-bottom: 24px;">GV</div>
        <form id="login-form">
            <input type="text" id="username" placeholder="HAC Username" required style="width:100%; margin-bottom:12px; padding:10px 12px; background:var(--surface-2); border:1px solid var(--border); color:var(--text-1); font-family:Inter; border-radius:4px;">
            <input type="password" id="password" placeholder="HAC Password" required style="width:100%; margin-bottom:20px; padding:10px 12px; background:var(--surface-2); border:1px solid var(--border); color:var(--text-1); font-family:Inter; border-radius:4px;">
            <button type="submit" style="width:100%; padding:12px; background:var(--text-1); color:var(--bg); border:none; border-radius:4px; font-weight:600; cursor:pointer;" id="login-btn">Sign In</button>
            <div id="login-error" style="color:var(--danger); margin-top:12px; font-size:12px; text-align:center;"></div>
        </form>
    </div>
</div>

<!-- Assignments Modal -->
<div id="assignments-modal" style="position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:9998; display:none; justify-content:center; align-items:center; backdrop-filter:blur(4px);">
    <div style="background:var(--surface); border:1px solid var(--border); border-radius:4px; width:80%; max-width:700px; max-height:80vh; display:flex; flex-direction:column;">
        <div style="padding:20px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center;">
            <h2 id="modal-course-title" style="font-family:Inter; font-size:18px; font-weight:600;">Course</h2>
            <button onclick="closeModal()" style="background:none; border:none; color:var(--text-2); cursor:pointer; font-size:24px;">&times;</button>
        </div>
        <div id="modal-assignments-list" style="padding:20px; overflow-y:auto; flex:1; font-family:'JetBrains Mono'; font-size:12px;">
            Loading...
        </div>
    </div>
</div>

<script>
  let theme = 'INK';
  let sessionId = localStorage.getItem('sessionId') || null;
  let allGradesData = [];

  function toggleTheme() {
    theme = theme === 'INK' ? 'PAPER' : 'INK';
    document.documentElement.setAttribute('data-theme', theme);
  }

  // Auth logic
  if(sessionId) {
      document.getElementById('login-overlay').style.display = 'none';
      fetchGrades();
  }

  document.getElementById('login-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const u = document.getElementById('username').value;
      const p = document.getElementById('password').value;
      const btn = document.getElementById('login-btn');
      btn.textContent = 'Authenticating...';
      
      try {
          const res = await fetch('/api/login', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ username:u, password:p })
          });
          const data = await res.json();
          if(!res.ok) throw new Error(data.error || 'Login failed');
          
          sessionId = data.session_id;
          localStorage.setItem('sessionId', sessionId);
          localStorage.setItem('cachedUsername', u);
          localStorage.setItem('cachedPassword', p);
          
          document.getElementById('login-overlay').style.display = 'none';
          fetchGrades();
      } catch(err) {
          document.getElementById('login-error').textContent = err.message;
      } finally {
          btn.textContent = 'Sign In';
      }
  });

  async function fetchWithAuth(url, options = {}) {
      if(!options.headers) options.headers = {};
      options.headers['X-Session-ID'] = sessionId;
      let res = await fetch(url, options);
      if(res.status === 401) {
          // auto reauth
          const u = localStorage.getItem('cachedUsername');
          const p = localStorage.getItem('cachedPassword');
          if(u && p) {
              const loginRes = await fetch('/api/login', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ username:u, password:p })
              });
              const loginData = await loginRes.json();
              if(loginData.session_id) {
                  sessionId = loginData.session_id;
                  localStorage.setItem('sessionId', sessionId);
                  options.headers['X-Session-ID'] = sessionId;
                  res = await fetch(url, options);
              } else { logout(); }
          } else { logout(); }
      }
      return res;
  }

  async function fetchGrades(cycle = '') {
      document.getElementById('status-bar').innerText = 'Syncing...';
      const url = cycle ? `/api/grades?cycle=${encodeURIComponent(cycle)}` : `/api/grades`;
      try {
          const res = await fetchWithAuth(url);
          const data = await res.json();
          if(!res.ok) throw new Error(data.error);
          
          updateUI(data);
      } catch(err) {
          console.error(err);
          document.getElementById('status-bar').innerText = 'Error syncing grades';
      }
  }

  function updateUI(data) {
      allGradesData = data.grades || [];
      const grid = document.getElementById('course-grid');
      grid.innerHTML = '';
      
      let highest = -1, lowest = 200, total = 0, count = 0;
      let highestName = '', lowestName = '';

      allGradesData.forEach(c => {
          if(c.numeric_grade !== null) {
              const g = parseFloat(c.numeric_grade);
              total += g; count++;
              if(g > highest) { highest = g; highestName = c.course_name; }
              if(g < lowest) { lowest = g; lowestName = c.course_name; }
          }
          
          const gStr = c.numeric_grade !== null ? `${c.numeric_grade}%` : '--%';
          const colorClass = c.numeric_grade !== null && c.numeric_grade < 70 ? 'var(--danger)' : 'var(--text-1)';
          
          grid.innerHTML += `
            <div class="course-card" onclick="openAssignments('${c.course_id}', '${c.course_name}')">
              <div class="card-top">
                <div>
                  <div class="card-code mono">${c.course_id}</div>
                  <div class="card-name">${c.course_name}</div>
                </div>
                <div class="status-dot" style="background:${c.last_updated && c.last_updated.toLowerCase() === 'just now' ? '#22C55E' : 'var(--text-3)'}"></div>
              </div>
              <div class="card-grade mono" style="color: ${colorClass};">${gStr}</div>
              <div class="card-code mono" style="margin-top:auto; font-size:10px; color:var(--text-3); text-align:right;">Updated: ${c.last_updated || 'Unknown'}</div>
            </div>
          `;
      });
      
      let avg = count > 0 ? (total/count).toFixed(2) : 0;
      
      document.getElementById('overall-avg').innerText = avg + '%';
      document.getElementById('highest-grade').innerText = highest === -1 ? '--%' : (highest + '%');
      document.getElementById('lowest-grade').innerText = lowest === 200 ? '--%' : (lowest + '%');
      
      document.getElementById('status-bar').innerText = `${avg}% overall \u00B7 ${count} courses \u00B7 cycle ${data.current_cycle || 5} \u00B7 synced`;
      
      if(data.current_cycle) {
          document.getElementById('cycle-num').innerText = data.current_cycle;
      }
  }

  async function openAssignments(courseId, courseName) {
      document.getElementById('assignments-modal').style.display = 'flex';
      document.getElementById('modal-course-title').innerText = courseName;
      document.getElementById('modal-assignments-list').innerHTML = 'Loading assignments...';
      
      try {
          const res = await fetchWithAuth(`/api/assignments/${encodeURIComponent(courseId)}`);
          const data = await res.json();
          if(!res.ok) throw new Error(data.error);
          
          let html = `<table style="width:100%; border-collapse:collapse; text-align:left;">`;
          html += `<tr style="border-bottom:1px solid var(--border); color:var(--text-2);">
                      <th style="padding:8px;">Date</th>
                      <th style="padding:8px;">Assignment</th>
                      <th style="padding:8px;">Category</th>
                      <th style="padding:8px;">Points</th>
                      <th style="padding:8px;">Score</th>
                   </tr>`;
          
          if(!data.categories || data.categories.length === 0) {
              html += `<tr><td colspan="5" style="padding:8px; text-align:center;">No assignments found</td></tr>`;
          } else {
              data.categories.forEach(cat => {
                  html += `<tr style="background:var(--surface-2); border-bottom:1px solid var(--border);"><td colspan="5" style="padding:8px; font-weight:600; font-family:Inter; font-size:11px; text-transform:uppercase;">${cat.name} (${cat.weight})</td></tr>`;
                  cat.assignments.forEach(a => {
                      html += `
                        <tr style="border-bottom:1px solid var(--border); border-top:1px solid var(--border);">
                          <td style="padding:8px; color:var(--text-2);">${a.date_due || '--'}</td>
                          <td style="padding:8px; color:var(--text-1); max-width:200px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${a.name}</td>
                          <td style="padding:8px; color:var(--text-2);">${a.category || '--'}</td>
                          <td style="padding:8px; color:var(--text-2);">${a.points || '--'}</td>
                          <td style="padding:8px; color:var(--text-1);">${a.score || '--'}</td>
                        </tr>
                      `;
                  });
              });
          }
          html += '</table>';
          document.getElementById('modal-assignments-list').innerHTML = html;
      } catch(err) {
          document.getElementById('modal-assignments-list').innerHTML = `<div style="color:var(--danger)">Error: ${err.message}</div>`;
      }
  }

  function closeModal() {
      document.getElementById('assignments-modal').style.display = 'none';
  }

  async function refresh() {
      document.getElementById('status-bar').innerText = 'Refreshing all cycles...';
      try {
          const res = await fetchWithAuth('/api/refresh_all_cycles', { method: 'POST' });
          if(!res.ok) throw new Error('Refesh failed');
          fetchGrades();
      } catch(err) {
          console.error(err);
          document.getElementById('status-bar').innerText = 'Refresh failed';
      }
  }

  function logout() {
      sessionId = null;
      localStorage.removeItem('sessionId');
      localStorage.removeItem('cachedUsername');
      localStorage.removeItem('cachedPassword');
      document.getElementById('login-overlay').style.display = 'flex';
      document.getElementById('course-grid').innerHTML = '';
  }
</script>
</body>
</html>
"""

with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(html + NEW_JS)

