import 'package:collection/collection.dart';
import 'package:equatable/equatable.dart';
import 'package:planner_repository/planner_repository.dart';

///
/// Degree year that represents a column with two semesters
/// and the subjects that are being done that year.
class DegreeYear extends Equatable {
  const DegreeYear({
    required this.year,
    required this.semesters,
    required this.yearNumber,
    this.isEditable = false,
    this.isRecommended = false,
  });

  final int year;
  final int yearNumber;
  final List<Semester> semesters;
  final bool isEditable;
  final bool isRecommended;

  Semester? semesterContainsSubject(PathSubject subject) {
    return semesters.firstWhereOrNull((semester) {
      return semester.subjects.any((s) => s == subject);
    });
  }

  bool containsEditableSemester() {
    return semesters.any((semester) => semester.isEditable);
  }

  DegreeYear copyWith({
    int? year,
    List<Semester>? semesters,
    int? yearNumber,
    bool? isEditable,
    bool? isRecommended,
  }) {
    return DegreeYear(
      year: year ?? this.year,
      semesters: semesters ?? this.semesters,
      yearNumber: yearNumber ?? this.yearNumber,
      isEditable: isEditable ?? this.isEditable,
      isRecommended: isRecommended ?? this.isRecommended,
    );
  }

  @override
  List<Object?> get props => [
        year,
        semesters,
        yearNumber,
        isEditable,
        isRecommended,
      ];
}

class Semester extends Equatable {
  const Semester({
    required this.year,
    required this.semester,
    required this.subjects,
    this.isRecommended = false,
    this.isRecommendationAccepted = false,
    this.isEditable = false,
  });

  const Semester.empty()
      : year = 0,
        semester = 0,
        subjects = const [],
        isRecommended = false,
        isRecommendationAccepted = false,
        isEditable = false;

  final int year;
  final double semester;
  final List<PathSubject> subjects;
  final bool isRecommended;
  final bool isRecommendationAccepted;
  final bool isEditable;

  bool get isEmpty => year == 0 && semester == 0;

  Semester copyWith({
    int? year,
    double? semester,
    List<PathSubject>? subjects,
    bool? isRecommended,
    bool? isRecommendationAccepted,
    bool? isEditable,
  }) {
    return Semester(
      year: year ?? this.year,
      semester: semester ?? this.semester,
      subjects: subjects ?? this.subjects,
      isRecommended: isRecommended ?? this.isRecommended,
      isRecommendationAccepted:
          isRecommendationAccepted ?? this.isRecommendationAccepted,
      isEditable: isEditable ?? this.isEditable,
    );
  }

  @override
  List<Object?> get props => [
        year,
        semester,
        subjects,
        isRecommended,
        isRecommendationAccepted,
        isEditable,
      ];
}
