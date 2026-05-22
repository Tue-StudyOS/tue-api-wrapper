package praxisportal

import (
	"encoding/json"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
)

var (
	berlinOnce sync.Once
	berlinLoc  *time.Location
)

func berlinLocation() *time.Location {
	berlinOnce.Do(func() {
		loc, err := time.LoadLocation("Europe/Berlin")
		if err != nil {
			berlinLoc = time.Local
			return
		}
		berlinLoc = loc
	})
	return berlinLoc
}

func asSlice(value any) []any {
	typed, ok := value.([]any)
	if !ok {
		return nil
	}
	return typed
}

func intOr(value any, fallback int) int {
	parsed, ok := safeInt(value)
	if !ok {
		return fallback
	}
	return parsed
}

func safeInt(value any) (int, bool) {
	switch typed := value.(type) {
	case int:
		return typed, true
	case int64:
		return int(typed), true
	case float64:
		return int(typed), true
	case float32:
		return int(typed), true
	case json.Number:
		parsed, err := typed.Int64()
		if err != nil {
			return 0, false
		}
		return int(parsed), true
	case string:
		parsed, err := strconv.Atoi(strings.TrimSpace(typed))
		if err != nil {
			return 0, false
		}
		return parsed, true
	default:
		return 0, false
	}
}

func asStringIntMap(value any) map[string]int {
	switch typed := value.(type) {
	case map[string]int:
		out := make(map[string]int, len(typed))
		for key, val := range typed {
			out[key] = val
		}
		return out
	case map[string]any:
		out := map[string]int{}
		for key, val := range typed {
			if parsed, ok := safeInt(val); ok {
				out[key] = parsed
			}
		}
		return out
	default:
		return map[string]int{}
	}
}

func keysAsInts(values map[string]int) []int {
	keys := make([]int, 0, len(values))
	for key := range values {
		parsed, err := strconv.Atoi(strings.TrimSpace(key))
		if err != nil {
			continue
		}
		keys = append(keys, parsed)
	}
	sort.Ints(keys)
	return keys
}
