package io.github.sebastianboehler.tueapi;

public final class TuebingenClient {
    private final AlmaApi alma;
    private final CampusApi campus;
    private final IliasApi ilias;
    private final MailApi mail;
    private final MoodleApi moodle;
    private final ProductApi products;
    private final TimmsApi timms;

    private TuebingenClient(int timeoutMillis, UniversityCredentials credentials) {
        this.alma = new AlmaApi(new HttpTransport(timeoutMillis), credentials);
        this.campus = new CampusApi(new HttpTransport(timeoutMillis));
        this.ilias = new IliasApi(new HttpTransport(timeoutMillis), credentials);
        this.mail = new MailApi(credentials);
        this.moodle = new MoodleApi(new HttpTransport(timeoutMillis), credentials);
        this.products = new ProductApi(new HttpTransport(timeoutMillis));
        this.timms = new TimmsApi(new HttpTransport(timeoutMillis));
    }

    public static Builder builder() {
        return new Builder();
    }

    public AlmaApi alma() {
        return alma;
    }

    public CampusApi campus() {
        return campus;
    }

    public IliasApi ilias() {
        return ilias;
    }

    public MailApi mail() {
        return mail;
    }

    public MoodleApi moodle() {
        return moodle;
    }

    public ProductApi products() {
        return products;
    }

    public TimmsApi timms() {
        return timms;
    }

    public static final class Builder {
        private int timeoutMillis = 30000;
        private UniversityCredentials credentials;

        public Builder credentials(String username, String password) {
            this.credentials = new UniversityCredentials(username, password);
            return this;
        }

        public Builder credentials(UniversityCredentials credentials) {
            this.credentials = credentials;
            return this;
        }

        public Builder timeoutMillis(int timeoutMillis) {
            this.timeoutMillis = timeoutMillis;
            return this;
        }

        public TuebingenClient build() {
            return new TuebingenClient(timeoutMillis, credentials);
        }
    }
}
