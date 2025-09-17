import 'package:education_planner/planner/planner.dart';
import 'package:planner_repository/planner_repository.dart';
import 'package:student_repository/student_repository.dart';

List<DegreeYear> buildDegreePlan(
  List<PathSubject> subjects,
  List<Subject> approvedSubjects,
) {
  final mapSemestersInYear = <int, List<double>>{
    1: [1.0, 2.0],
    2: [3.0, 4.0],
    3: [5.0, 6.0],
    4: [7.0, 8.0],
  };
  final degreePlan = <DegreeYear>[];
  var startYear = 1;
  const totalYears = 4;

  for (var i = 1; i < totalYears + 1; i++) {
    final semesters = mapSemestersInYear[i] ?? [];
    final subjectsInYear = subjects
        .where((subject) => semesters.contains(subject.semester))
        .map(
          (subject) =>
              approvedSubjects.any((s) => int.tryParse(s.code) == subject.id)
                  ? subject.copyWith(
                      status: 'APR',
                    )
                  : subject,
        )
        .toList();

    if (subjectsInYear.isNotEmpty) {
      final degreePlanYear = DegreeYear(
        year: startYear,
        yearNumber: i,
        semesters: semesters
            .map(
              (semester) => Semester(
                semester: semester,
                subjects: subjectsInYear
                    .where((subject) => subject.semester == semester)
                    .toList(),
                year: startYear,
              ),
            )
            .toList(),
      );
      startYear++;
      degreePlan.add(degreePlanYear);
    }
  }

  return degreePlan;
}
