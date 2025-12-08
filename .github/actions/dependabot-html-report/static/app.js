document.querySelectorAll('table thead th[data-sort]').forEach(th => {
  th.style.cursor = 'pointer';
  th.addEventListener('click', () => {
    const key = th.dataset.sort;
    const idx = th.cellIndex;
    const table = th.closest('table');
    const rows = Array.from(table.tBodies[0].rows);
    const asc = th.dataset.order !== 'desc';
    function val(row){
      const attr = row.getAttribute('data-' + key);
      if(attr) return attr;
      return row.cells[idx].innerText.trim();
    }
    rows.sort((a,b) => {
      let va = val(a), vb = val(b);
      if(key === 'num'){
        va = parseInt(String(va).replace(/[^0-9]/g,'')) || 0;
        vb = parseInt(String(vb).replace(/[^0-9]/g,'')) || 0;
        return asc ? va - vb : vb - va;
      }
      if(key === 'created'){
        const da = Date.parse(va) || 0;
        const db = Date.parse(vb) || 0;
        return asc ? da - db : db - da;
      }
      if(key === 'age'){
        va = parseInt(va) || 0;
        vb = parseInt(vb) || 0;
        return asc ? va - vb : vb - va;
      }
      return asc ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va));
    });
    rows.forEach(r => table.tBodies[0].appendChild(r));
    th.dataset.order = asc ? 'desc' : 'asc';
  });
});
