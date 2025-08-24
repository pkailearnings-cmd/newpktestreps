(function(){
	const textarea = document.getElementById('tailored');
	const scoreEl = document.getElementById('score');
	const matchedEl = document.getElementById('matched');
	const missingEl = document.getElementById('missing');
	const jobText = window.__JOB_TEXT__ || '';

	async function recalc(){
		const body = { resume_text: textarea.value, job_text: jobText };
		try {
			const resp = await fetch('/api/recalc', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(body)
			});
			if(!resp.ok){ return; }
			const data = await resp.json();
			scoreEl.textContent = (data.score || 0).toFixed(1);
			matchedEl.innerHTML = '';
			missingEl.innerHTML = '';
			(data.matched_keywords || []).forEach(kw => {
				const li = document.createElement('li');
				li.textContent = kw; matchedEl.appendChild(li);
			});
			(data.missing_keywords || []).forEach(kw => {
				const li = document.createElement('li');
				li.textContent = kw; missingEl.appendChild(li);
			});
		} catch(e) {
			// ignore
		}
	}

	let timer = null;
	textarea.addEventListener('input', () => {
		clearTimeout(timer);
		timer = setTimeout(recalc, 300);
	});
})();