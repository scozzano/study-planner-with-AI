import 'package:education_planner/bootstrap.dart';
import 'package:education_planner/main_common.dart';

void main() {
  const apiUrl = String.fromEnvironment('API_URL');

  bootstrap(() => mainCommon(apiUrl: apiUrl));
}
