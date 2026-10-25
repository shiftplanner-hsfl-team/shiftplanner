document.documentElement.classList.add('js');
for (const input of document.querySelectorAll('.priority')) {
  input.addEventListener('change', () => {
    input.className = `priority p${input.value}`;
    const partner = input.dataset.mirror
      ? document.getElementById(input.dataset.mirror)
      : document.querySelector(`[data-mirror="${input.id}"]`);
    if (partner) {
      partner.value = input.value;
      partner.className = `priority p${input.value}`;
    }
  });
}
for (const form of document.querySelectorAll('[data-busy]')) {
  form.addEventListener('submit', () => {
    const button = form.querySelector('button');
    button.disabled = true;
    button.textContent = 'Plan wird erzeugt …';
  });
}
// Warn only when navigating away from unsaved form edits.
let dirty = false;
for (const form of document.querySelectorAll('#demand-form, #availability-form')) {
  form.addEventListener('change', () => { dirty = true; });
  form.addEventListener('submit', () => { dirty = false; });
}
window.addEventListener('beforeunload', event => {
  if (dirty) { event.preventDefault(); event.returnValue = ''; }
});

for (const button of document.querySelectorAll('[data-show-days]')) {
  const extras = document.querySelectorAll('[data-extra-day]');
  if (!extras.length) button.hidden = true;
  button.addEventListener('click', () => {
    for (const day of extras) day.hidden = false;
    button.hidden = true;
  });
}
