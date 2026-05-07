package io.github.sebastianboehler.tueapi;

public class TueApiException extends Exception {
    private final int statusCode;
    private final String responseBody;

    public TueApiException(String message) {
        super(message);
        this.statusCode = 0;
        this.responseBody = "";
    }

    public TueApiException(int statusCode, String responseBody) {
        super("tue-api-wrapper request failed with HTTP " + statusCode);
        this.statusCode = statusCode;
        this.responseBody = responseBody == null ? "" : responseBody;
    }

    public int getStatusCode() {
        return statusCode;
    }

    public String getResponseBody() {
        return responseBody;
    }
}
