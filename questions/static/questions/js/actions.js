(() => {
  const errorBanner = document.querySelector('[data-action-error]');

  function showError(message = '') {
    errorBanner.textContent = message;
    errorBanner.hidden = message === '';
  }

  async function submit(form, fields) {
    const body = new FormData(form);
    for (const [name, value] of Object.entries(fields)) {
      body.set(name, value);
    }

    let response;
    try {
      response = await fetch(form.action, {
        method: 'POST',
        body,
        headers: { Accept: 'application/json' },
      });
    } catch {
      throw new Error('Связь с сервером прервалась. Попробуйте ещё раз.');
    }

    const data = await response.json().catch(() => ({}));
    if (response.status === 401 && data.login_url) {
      const login = new URL(data.login_url, window.location.origin);
      login.searchParams.set('next', window.location.pathname + window.location.search + window.location.hash);
      window.location.assign(login);
      throw new Error(data.error);
    }
    if (!response.ok) {
      throw new Error(data.error || 'Сервер не принял запрос. Попробуйте ещё раз.');
    }
    return data;
  }

  document.addEventListener('submit', async (event) => {
    const form = event.target;
    if (!form.matches('[data-vote-form]')) return;

    event.preventDefault();
    const button = event.submitter;
    if (!button || button.disabled) return;

    const buttons = [...form.querySelectorAll('button')];
    const value = button.getAttribute('aria-pressed') === 'true' ? '0' : button.value;
    buttons.forEach((control) => { control.disabled = true; });
    showError();

    try {
      const result = await submit(form, { value });
      form.querySelector('.vote-count').textContent = result.rating;
      form.dataset.state = result.vote === 1 ? 'up' : result.vote === -1 ? 'down' : 'none';
      for (const control of buttons) {
        const pressed = Number(control.value) === result.vote;
        control.classList.toggle('active', pressed);
        control.setAttribute('aria-pressed', String(pressed));
      }
    } catch (error) {
      showError(error.message);
    } finally {
      buttons.forEach((control) => { control.disabled = false; });
    }
  });

  document.addEventListener('change', async (event) => {
    const input = event.target;
    if (!input.matches('[data-correct-form] input[type="checkbox"]')) return;

    const checkboxes = document.querySelectorAll('[data-correct-form] input[type="checkbox"]');
    const accepted = input.checked ? '1' : '0';
    checkboxes.forEach((control) => { control.disabled = true; });
    showError();

    try {
      const result = await submit(input.form, { accepted });
      for (const card of document.querySelectorAll('[data-answer-id]')) {
        const correct = card.dataset.answerId === String(result.correct_answer_id);
        card.classList.toggle('answer-correct', correct);
        card.querySelector('[data-correct-badge]').hidden = !correct;
        const control = card.querySelector('[data-correct-form] input[type="checkbox"]');
        if (control) {
          control.defaultChecked = correct;
          control.checked = correct;
        }
      }
    } catch (error) {
      input.checked = input.defaultChecked;
      showError(error.message);
    } finally {
      checkboxes.forEach((control) => { control.disabled = false; });
    }
  });
})();
