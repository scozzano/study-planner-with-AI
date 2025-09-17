import 'package:collection/collection.dart';
import 'package:education_planner/planner/models/degree_year.dart';
import 'package:education_planner/planner/widgets/student_plan.dart';
import 'package:planner_repository/planner_repository.dart';

extension XDegreeYearList on List<DegreeYear> {
  DegreeYear? findSubject(PathSubject subject) {
    return firstWhereOrNull(
      (year) => year.semesterContainsSubject(subject) != null,
    );
  }

  DegreeYear? findBySemester(Semester semester) {
    return firstWhereOrNull(
      (year) => year.semesters.any((s) => s == semester),
    );
  }

  List<DegreeYear> addNewSubjectsToPlan({
    required List<PathSubject> subjects,
  }) {
    final addsNewSemester = last.semesters.length < 2;
    if (addsNewSemester) {
      return addNewSemester(
        selectedSubjects: subjects,
      );
    }
    return addNewYear(
      selectedSubjects: subjects,
    );
  }

  List<DegreeYear> addNewSemester({
    required List<PathSubject> selectedSubjects,
    bool isRecommended = false,
  }) {
    final lastPlannedYear = last;

    final updatedSemesters = List<Semester>.from(lastPlannedYear.semesters)
      ..add(
        Semester(
          year: lastPlannedYear.year,
          semester: lastPlannedYear.semesters.first.semester + 1,
          subjects: selectedSubjects,
          isRecommended: isRecommended,
          isEditable: true,
        ),
      );
    final updatedLastPlanYear = lastPlannedYear.copyWith(
      semesters: updatedSemesters,
    );

    return List<DegreeYear>.from(this)
      ..removeLast()
      ..add(updatedLastPlanYear);
  }

  List<DegreeYear> addNewYear({
    required List<PathSubject> selectedSubjects,
  }) {
    final lastYear = last.year + 1;
    final year = isNotEmpty ? lastYear : DateTime.now().year;
    final degreeYear = DegreeYear(
      year: year,
      semesters: [
        Semester(
          year: year,
          semester: last.semesters.last.semester + 1,
          subjects: selectedSubjects,
          isEditable: true,
        ),
      ],
      yearNumber: last.yearNumber + 1,
      isEditable: true,
    );

    return List<DegreeYear>.from(this)..add(degreeYear);
  }

  List<DegreeYear> addSubjectToSemester({
    required SelectedSemester selectedSemester,
  }) {
    final plan = List<DegreeYear>.from(this);
    final yearToUpdate = plan.findBySemester(selectedSemester.semester);

    if (yearToUpdate == null) return plan;

    final updatedSemester = yearToUpdate.semesters.map((s) {
      if (s.semester == selectedSemester.semester.semester) {
        // Filter out subjects that already exist to prevent duplicates
        final existingSubjectIds =
            s.subjects.map((subject) => subject.id).toSet();
        final newSubjects = selectedSemester.subjects
            .where((subject) => !existingSubjectIds.contains(subject.id))
            .toList();

        return s.copyWith(subjects: [...s.subjects, ...newSubjects]);
      }
      return s;
    }).toList();

    final updatedYear = yearToUpdate.copyWith(semesters: updatedSemester);
    plan
      ..remove(yearToUpdate)
      ..add(updatedYear)
      ..sort((a, b) => a.year.compareTo(b.year));

    return plan;
  }

  List<DegreeYear> updateSubjects({
    required List<PathSubject> newSubjects,
  }) {
    return map((year) {
      final updatedSemesters = year.semesters.map((semester) {
        final updatedSubjects = semester.subjects.map((subject) {
          // Find matching subject with success rate
          final updatedSubject = newSubjects.firstWhereOrNull(
            (s) => s.id == subject.id && s.name == subject.name,
          );

          if (updatedSubject != null) {
            return updatedSubject;
          }

          return subject;
        }).toList();

        return semester.copyWith(subjects: updatedSubjects);
      }).toList();

      return year.copyWith(semesters: updatedSemesters);
    }).toList();
  }
}
