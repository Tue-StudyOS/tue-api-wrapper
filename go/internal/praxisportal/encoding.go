package praxisportal

import (
	"fmt"
	"strings"
	"unicode/utf8"
)

func quote(value string, safe string) string {
	allowed := map[rune]struct{}{}
	for _, ch := range safe {
		allowed[ch] = struct{}{}
	}

	var out strings.Builder
	for _, ch := range value {
		if ch == ' ' {
			out.WriteString("%20")
			continue
		}
		if isUnreserved(ch) {
			out.WriteRune(ch)
			continue
		}
		if _, ok := allowed[ch]; ok {
			out.WriteRune(ch)
			continue
		}
		var buf [utf8.UTFMax]byte
		n := utf8.EncodeRune(buf[:], ch)
		for i := 0; i < n; i++ {
			out.WriteString(fmt.Sprintf("%%%02X", buf[i]))
		}
	}
	return out.String()
}

func isUnreserved(ch rune) bool {
	if ch >= 'a' && ch <= 'z' {
		return true
	}
	if ch >= 'A' && ch <= 'Z' {
		return true
	}
	if ch >= '0' && ch <= '9' {
		return true
	}
	switch ch {
	case '-', '.', '_', '~':
		return true
	default:
		return false
	}
}
