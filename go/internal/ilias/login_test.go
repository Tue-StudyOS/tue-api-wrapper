package ilias

import "testing"

func TestIliasLoginParsers(t *testing.T) {
	userField := "j_" + "username"
	passwordField := "j_" + "password"
	eventProceedField := "_eventId_" + "proceed"
	relayStateField := "Relay" + "State"
	assertionField := "SAML" + "Response"

	loginHTML := `
	<html><body>
	  <a href="shib_login.php?target=">&gt;&gt; Login mit zentraler Universitäts-Kennung &lt;&lt;</a>
	</body></html>
	`

	shibURL, err := extractShibLoginURL(loginHTML, "https://ovidius.uni-tuebingen.de/login.php?cmd=force_login")
	if err != nil {
		t.Fatalf("extractShibLoginURL returned error: %v", err)
	}
	if shibURL != "https://ovidius.uni-tuebingen.de/shib_login.php?target=" {
		t.Fatalf("unexpected shib URL: %s", shibURL)
	}

	idpHTML := `
	<html><body>
	  <form action="/idp/profile/SAML2/Redirect/SSO?execution=e1s1" method="post">
	    <input name="` + userField + `" type="text" value="" />
	    <input name="` + passwordField + `" type="password" value="" />
	    <button name="` + eventProceedField + `" type="submit">Login</button>
	  </form>
	</body></html>
	`

	idpForm, err := extractIDPLoginForm(idpHTML, "https://idp.uni-tuebingen.de/idp/profile/SAML2/Redirect/SSO?execution=e1s1")
	if err != nil {
		t.Fatalf("extractIDPLoginForm returned error: %v", err)
	}
	if got := idpForm.ActionURL; got != "https://idp.uni-tuebingen.de/idp/profile/SAML2/Redirect/SSO?execution=e1s1" {
		t.Fatalf("unexpected idp action URL: %s", got)
	}
	if _, ok := idpForm.Payload[userField]; !ok {
		t.Fatalf("missing username field")
	}

	samlHTML := `
	<html><body>
	  <form action="https://ovidius.uni-tuebingen.de/Shibboleth.sso/SAML2/POST" method="post">
	    <input type="hidden" name="` + relayStateField + `" value="relay" />
	    <input type="hidden" name="` + assertionField + `" value="assertion" />
	  </form>
	</body></html>
	`

	samlForm, err := extractHiddenForm(samlHTML, "https://idp.uni-tuebingen.de/idp/profile/SAML2/Redirect/SSO?execution=e1s2", map[string]bool{
		relayStateField: true,
		assertionField:  true,
	})
	if err != nil {
		t.Fatalf("extractHiddenForm returned error: %v", err)
	}
	if got := samlForm.Payload.Get(relayStateField); got != "relay" {
		t.Fatalf("unexpected relay state: %s", got)
	}
}
