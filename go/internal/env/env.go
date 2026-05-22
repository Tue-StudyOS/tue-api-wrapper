package env

import (
	"bufio"
	"os"
	"path/filepath"
	"strings"
)

func LoadLocalEnv(paths ...string) error {
	workingDir, err := os.Getwd()
	if err != nil {
		return err
	}

	directories := parentDirs(workingDir)
	for _, directory := range directories {
		for _, path := range paths {
			if err := loadFile(filepath.Join(directory, path)); err != nil {
				return err
			}
		}
	}
	return nil
}

func AlmaCredentials() (string, string) {
	return sharedCredentials()
}

func IliasCredentials() (string, string) {
	return sharedCredentials()
}

func sharedCredentials() (string, string) {
	return firstNonEmpty(
			os.Getenv("UNI_USERNAME"),
			os.Getenv("ALMA_USERNAME"),
			os.Getenv("ILIAS_USERNAME"),
		), firstNonEmpty(
			os.Getenv("UNI_PASSWORD"),
			os.Getenv("ALMA_PASSWORD"),
			os.Getenv("ILIAS_PASSWORD"),
		)
}

func firstNonEmpty(values ...string) string {
	for _, value := range values {
		if value != "" {
			return value
		}
	}
	return ""
}

func loadFile(path string) error {
	file, err := os.Open(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		key, value, ok := strings.Cut(line, "=")
		if !ok {
			continue
		}

		key = strings.TrimSpace(key)
		if key == "" || os.Getenv(key) != "" {
			continue
		}

		value = strings.TrimSpace(value)
		value = strings.Trim(value, `"'`)
		if err := os.Setenv(key, value); err != nil {
			return err
		}
	}

	return scanner.Err()
}

func parentDirs(start string) []string {
	seen := map[string]bool{}
	var directories []string
	current := start

	for {
		if !seen[current] {
			seen[current] = true
			directories = append(directories, current)
		}
		parent := filepath.Dir(current)
		if parent == current {
			break
		}
		current = parent
	}

	return directories
}
