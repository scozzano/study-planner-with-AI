import 'package:shared_preferences/shared_preferences.dart';

class SharedPreferencesHelper {
  static const String _studentIdKey = 'studentId';

  static Future<void> setStudentId(String studentId) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_studentIdKey, studentId);
  }

  static Future<String?> getStudentId() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_studentIdKey);
  }
}
