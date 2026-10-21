function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta) return meta.content;
  const input = document.querySelector('input[name="csrf_token"]');
  return input ? input.value : '';
}

function bufferToBase64url(buffer) {
  const bytes = new Uint8Array(buffer);
  let str = '';
  for (const b of bytes) str += String.fromCharCode(b);
  return btoa(str).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function base64urlToBuffer(base64url) {
  const padding = '='.repeat((4 - (base64url.length % 4)) % 4);
  const base64 = (base64url + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(base64);
  const buffer = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) buffer[i] = raw.charCodeAt(i);
  return buffer.buffer;
}

function prepareCredentialOptions(options) {
  const prepared = { ...options };
  prepared.challenge = base64urlToBuffer(options.challenge);
  if (options.allowCredentials) {
    prepared.allowCredentials = options.allowCredentials.map(c => ({
      ...c,
      id: base64urlToBuffer(c.id),
    }));
  }
  if (options.excludeCredentials) {
    prepared.excludeCredentials = options.excludeCredentials.map(c => ({
      ...c,
      id: base64urlToBuffer(c.id),
    }));
  }
  if (options.user && options.user.id) {
    prepared.user = { ...options.user, id: base64urlToBuffer(options.user.id) };
  }
  return prepared;
}

function credentialToJSON(credential) {
  const response = credential.response;
  const result = {
    id: credential.id,
    rawId: bufferToBase64url(credential.rawId),
    type: credential.type,
    response: {
      clientDataJSON: bufferToBase64url(response.clientDataJSON),
    },
  };
  if (response.attestationObject) {
    result.response.attestationObject = bufferToBase64url(response.attestationObject);
  }
  if (response.authenticatorData) {
    result.response.authenticatorData = bufferToBase64url(response.authenticatorData);
    result.response.signature = bufferToBase64url(response.signature);
  }
  return result;
}

async function passkeyRegister(deviceName) {
  const csrf = getCsrfToken();
  const beginRes = await fetch('/passkey/register/begin', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
    credentials: 'same-origin',
  });
  if (!beginRes.ok) throw new Error('Kon registratie niet starten');
  const options = await beginRes.json();
  const credential = await navigator.credentials.create({
    publicKey: prepareCredentialOptions(options),
  });
  const data = credentialToJSON(credential);
  data.device_name = deviceName;
  const completeRes = await fetch('/passkey/register/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
    credentials: 'same-origin',
    body: JSON.stringify(data),
  });
  if (!completeRes.ok) {
    const err = await completeRes.json();
    throw new Error(err.error || 'Registratie mislukt');
  }
  return await completeRes.json();
}

async function passkeyLogin(username) {
  const csrf = getCsrfToken();
  const beginRes = await fetch('/passkey/login/begin', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
    credentials: 'same-origin',
    body: JSON.stringify({ username: username || '' }),
  });
  if (!beginRes.ok) throw new Error('Kon inloggen niet starten');
  const options = await beginRes.json();
  const credential = await navigator.credentials.get({
    publicKey: prepareCredentialOptions(options),
  });
  const data = credentialToJSON(credential);
  const completeRes = await fetch('/passkey/login/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
    credentials: 'same-origin',
    body: JSON.stringify(data),
  });
  if (!completeRes.ok) {
    const err = await completeRes.json();
    throw new Error(err.error || 'Inloggen mislukt');
  }
  const result = await completeRes.json();
  window.location.href = result.redirect || '/dashboard';
}

window.passkeyRegister = passkeyRegister;
window.passkeyLogin = passkeyLogin;
