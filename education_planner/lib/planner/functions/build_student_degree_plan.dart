import 'package:collection/collection.dart';
import 'package:education_planner/planner/planner.dart';
import 'package:planner_repository/planner_repository.dart';
import 'package:student_repository/student_repository.dart';

List<DegreeYear> buildStudentDegreePlan({
  required Schooling schooling,
}) {
  final subjects = List<Subject>.from(schooling.subjects)
    ..removeWhere((subject) => !subject.isApproved)
    ..removeWhere(
      (subject) => subject.date == null,
    );
  final groupedSubjectsByMonth = groupBy(subjects, (Subject s) {
    final month = s.date!.month;
    final semester = month >= 1 && month <= 8 ? 1 : 2;
    return DateTime(s.date!.year, semester);
  });
  final sortedGroupedSubjectsByMonth = Map.fromEntries(
    groupedSubjectsByMonth.entries.toList()
      ..sort((a, b) => a.key.compareTo(b.key)),
  );
  final semestersByYear = <int, List<Semester>>{};
  var semesterNumber = 1.0;

  final degreePlan = <DegreeYear>[];

  sortedGroupedSubjectsByMonth.forEach((date, subjects) {
    final year = date.year;

    final semester = Semester(
      semester: semesterNumber,
      year: year,
      subjects: subjects.map((subject) {
        return PathSubject(
          id: int.parse(subject.code),
          name: subject.name,
          semester: semesterNumber,
          status: subject.status,
        );
      }).toList(),
    );

    if (semestersByYear[year] == null) {
      semestersByYear[year] = [];
    }
    semestersByYear[year]!.add(semester);
    semesterNumber++;
  });

  for (final entry in semestersByYear.entries) {
    final year = entry.key;
    final semester = entry.value;

    final degreePlanEntry = DegreeYear(
      year: year,
      yearNumber: year,
      semesters: semester,
    );

    degreePlan.add(degreePlanEntry);
  }

  return degreePlan;
}

double getSemesterByDate(DateTime? date) {
  if (date == null) {
    return 0;
  }
  final month = date.month;
  if (month >= 1 && month <= 6) {
    return 1;
  } else if (month >= 7 && month <= 12) {
    return 2;
  }
  return 0;
}
