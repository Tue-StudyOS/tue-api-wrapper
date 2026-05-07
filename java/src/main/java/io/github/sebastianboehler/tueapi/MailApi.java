package io.github.sebastianboehler.tueapi;

import java.util.Properties;
import javax.mail.Address;
import javax.mail.Folder;
import javax.mail.Message;
import javax.mail.Session;
import javax.mail.Store;

public final class MailApi {
    private static final String HOST = "mailserv.uni-tuebingen.de";
    private final UniversityCredentials credentials;

    MailApi(UniversityCredentials credentials) {
        this.credentials = credentials;
    }

    public String mailboxes() throws Exception {
        Store store = store();
        try {
            Folder[] folders = store.getDefaultFolder().list("*");
            StringBuilder json = new StringBuilder("[");
            for (int i = 0; i < folders.length; i++) {
                if (i > 0) {
                    json.append(",");
                }
                json.append("{").append(JsonSupport.pair("name", folders[i].getFullName())).append("}");
            }
            return json.append("]").toString();
        } finally {
            store.close();
        }
    }

    public String inbox(int limit, boolean unreadOnly, String query) throws Exception {
        Store store = store();
        Folder folder = store.getFolder("INBOX");
        try {
            folder.open(Folder.READ_ONLY);
            Message[] messages = folder.getMessages();
            StringBuilder json = new StringBuilder("[");
            int count = 0;
            for (int i = messages.length - 1; i >= 0 && count < limit; i--) {
                Message message = messages[i];
                String subject = safe(message.getSubject());
                if (query != null && !query.isEmpty() && !subject.toLowerCase().contains(query.toLowerCase())) {
                    continue;
                }
                if (count++ > 0) {
                    json.append(",");
                }
                json.append("{")
                    .append(JsonSupport.pair("subject", subject)).append(",")
                    .append(JsonSupport.pair("from", addresses(message.getFrom()))).append(",")
                    .append(JsonSupport.pair("sent_at", message.getSentDate() == null ? null : message.getSentDate().toString()))
                    .append("}");
            }
            return json.append("]").toString();
        } finally {
            folder.close(false);
            store.close();
        }
    }

    private Store store() throws Exception {
        if (credentials == null) {
            throw new TueApiException("Mail calls require UniversityCredentials.");
        }
        Properties properties = new Properties();
        properties.put("mail.store.protocol", "imaps");
        properties.put("mail.imaps.host", HOST);
        properties.put("mail.imaps.port", "993");
        Session session = Session.getInstance(properties);
        Store store = session.getStore("imaps");
        store.connect(HOST, credentials.username(), credentials.password());
        return store;
    }

    private static String addresses(Address[] addresses) {
        if (addresses == null || addresses.length == 0) {
            return null;
        }
        StringBuilder builder = new StringBuilder();
        for (Address address : addresses) {
            if (builder.length() > 0) {
                builder.append(", ");
            }
            builder.append(address.toString());
        }
        return builder.toString();
    }

    private static String safe(String value) {
        return value == null ? "" : value;
    }
}
