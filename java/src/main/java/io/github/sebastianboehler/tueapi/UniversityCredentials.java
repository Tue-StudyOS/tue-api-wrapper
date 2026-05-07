package io.github.sebastianboehler.tueapi;

public final class UniversityCredentials {
    private final String username;
    private final String password;

    public UniversityCredentials(String username, String password) {
        this.username = username;
        this.password = password;
    }

    public String username() {
        return username;
    }

    public String password() {
        return password;
    }
}
