(function(){
  async function api(path){
    const res = await fetch(path, {credentials: 'same-origin'});
    if (!res.ok) throw new Error('API error');
    return res.json();
  }

  function render(data){
    const out = document.getElementById('workout-list');
    if (!data || !data.tables || data.tables.length === 0){
      out.innerHTML = '<p>No workouts yet.</p>';
      return;
    }
    const html = data.tables.map(t => {
      const rows = (t.rows||[]).map(r => `<li>${r.day_number} • ${r.exercise_name} — set ${r.set_number} — ${r.rep_goal} reps @ ${r.weight}kg</li>`).join('');
      return `<section class="table"><h2>${t.name}</h2><ul>${rows}</ul></section>`;
    }).join('');
    out.innerHTML = html;
  }

  async function init(){
    try{
      const params = new URLSearchParams(window.location.search);
      const member_id = params.get('member_id');
      const q = member_id ? `/api/plan?member_id=${member_id}` : '/api/plan';
      const data = await api(q);
      render(data);
    }catch(err){
      document.getElementById('workout-list').innerText = 'Failed to load workouts.';
      console.error(err);
    }
  }

  document.addEventListener('DOMContentLoaded', init);
})();
