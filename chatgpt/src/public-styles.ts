export const publicStyles = `
:root{color-scheme:light dark;font:16px/1.6 system-ui,sans-serif;color:light-dark(#202123,#ececec);background:light-dark(#fff,#212121)}
*{box-sizing:border-box}body{margin:0}main{max-width:720px;margin:0 auto;padding:48px 24px}
h1{font-size:28px;line-height:1.2;margin:0 0 24px}p{margin:0 0 16px}nav{margin-top:32px}
a{color:inherit;text-underline-offset:3px}form{display:grid;gap:16px;margin:24px 0}
label{display:grid;gap:8px}input,button{font:inherit;min-height:44px;border:1px solid light-dark(#d9d9d9,#555);border-radius:8px;padding:8px 12px}
button{cursor:pointer;background:light-dark(#202123,#ececec);color:light-dark(#fff,#202123)}
:focus-visible{outline:2px solid currentColor;outline-offset:3px}@media(max-width:480px){main{padding:24px 16px}h1{font-size:24px}}
`;
