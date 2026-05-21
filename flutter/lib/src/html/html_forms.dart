import 'package:html/dom.dart';
import 'package:html/parser.dart' as html_parser;

class HtmlForm {
  HtmlForm({required this.action, required this.fields});

  final Uri action;
  final Map<String, String> fields;

  void set(String name, String? value) {
    fields[name] = value ?? '';
  }
}

Document parseHtml(String html, Uri pageUri) {
  return html_parser.parse(html, sourceUrl: pageUri.toString());
}

HtmlForm formById(String html, Uri pageUri, String id) {
  final document = parseHtml(html, pageUri);
  final form = document.querySelector('form#$id');
  if (form == null) {
    throw StateError('Could not find form #$id.');
  }
  return formFromElement(form, pageUri);
}

HtmlForm formWithInput(String html, Uri pageUri, String inputName) {
  final document = parseHtml(html, pageUri);
  for (final form in document.querySelectorAll('form')) {
    if (form.querySelector('[name="$inputName"]') != null) {
      return formFromElement(form, pageUri);
    }
  }
  throw StateError('Could not find form with input $inputName.');
}

HtmlForm hiddenFormWithFields(
    String html, Uri pageUri, Iterable<String> fields) {
  final document = parseHtml(html, pageUri);
  for (final form in document.querySelectorAll('form')) {
    final matches =
        fields.every((field) => form.querySelector('[name="$field"]') != null);
    if (matches) {
      return formFromElement(form, pageUri);
    }
  }
  throw StateError('Could not find hidden handoff form.');
}

HtmlForm formFromElement(Element form, Uri pageUri) {
  final fields = <String, String>{};
  for (final field
      in form.querySelectorAll('input[name], select[name], textarea[name]')) {
    final name = field.attributes['name'];
    if (name == null || field.attributes.containsKey('disabled')) {
      continue;
    }
    final type = (field.attributes['type'] ?? '').toLowerCase();
    if (const {'button', 'file', 'image', 'reset'}.contains(type)) {
      continue;
    }
    if ((type == 'checkbox' || type == 'radio') &&
        !field.attributes.containsKey('checked')) {
      continue;
    }
    fields[name] = _fieldValue(field);
  }
  final action = form.attributes['action'];
  return HtmlForm(action: pageUri.resolve(action ?? ''), fields: fields);
}

String cleanText(Element element) {
  return element.text.replaceAll(RegExp(r'\s+'), ' ').trim();
}

String? nullableText(Element? element) {
  if (element == null) {
    return null;
  }
  final value = cleanText(element);
  return value.isEmpty ? null : value;
}

String _fieldValue(Element field) {
  if (field.localName == 'select') {
    final selected = field.querySelector('option[selected]') ??
        field.querySelector('option');
    if (selected == null) {
      return '';
    }
    return selected.attributes['value'] ?? selected.text;
  }
  return field.attributes['value'] ?? field.text;
}
