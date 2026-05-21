Future<LoadResult<T>> captureLoad<T>(
    String label, Future<T> Function() action) async {
  try {
    return LoadResult(label: label, value: await action());
  } catch (error) {
    return LoadResult(
        label: label, warning: '$label could not be loaded: $error');
  }
}

class LoadResult<T> {
  const LoadResult({required this.label, this.value, this.warning});

  final String label;
  final T? value;
  final String? warning;
}
