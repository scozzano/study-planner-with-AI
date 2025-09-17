import 'package:planner_repository/planner_repository.dart';
import 'package:student_repository/student_repository.dart';

extension XPathSubjectList on List<PathSubject> {
  List<PathSubject> filterNotApprovedSubjects({
    required List<Subject> schoolingSubjects,
    required List<PathSubject> modifiedDegreePlanSubjects,
  }) {
    return where(
      (subject) =>
          !schoolingSubjects.any((s) => s.code == subject.id.toString()) ||
          !modifiedDegreePlanSubjects.any((s) => s.id == subject.id),
    ).toList();
  }
}
