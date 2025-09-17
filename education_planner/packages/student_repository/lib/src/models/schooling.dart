import 'package:equatable/equatable.dart';
import 'package:intl/intl.dart';
import 'package:json_annotation/json_annotation.dart';
import 'package:student_repository/student_repository.dart';

part 'schooling.g.dart';

@JsonSerializable(explicitToJson: true)

/// Represents a schooling record for a student.
class Schooling extends Equatable {
  /// Creates a new instance of [Schooling].
  const Schooling({
    required this.id,
    required this.name,
    required this.document,
    required this.enrollmentNumber,
    required this.title,
    required this.plan,
    required this.startDate,
    required this.averageGrade,
    required this.averageApprovedGrade,
    required this.subjectsRequired,
    required this.subjectsObtained,
    required this.failedSubjects,
    required this.subjects,
    this.graduationDate,
  });

  /// Creates a new instance of [Schooling] from a JSON object.
  factory Schooling.fromJson(Map<String, dynamic> json) =>
      _$SchoolingFromJson(json);

  /// Converts the [Schooling] instance to a JSON object.
  Map<String, dynamic> toJson() => _$SchoolingToJson(this);

  /// Represents the unique identifier for the schooling record.
  final String? id;

  /// The name of the schooling institution or program.
  final String? name;

  /// The ID or document number of the student.
  final String? document;

  /// The enrollment number assigned to the student.
  @JsonKey(name: 'enrollment_number')
  final String? enrollmentNumber;

  /// The title or degree associated with the schooling program.
  final String? title;

  /// The academic plan or curriculum followed by the student.
  final String? plan;

  /// The date when the schooling program started.
  @JsonKey(
    name: 'start_date',
    fromJson: _dateTimeFromCustomFormat,
    toJson: _dateTimeToCustomFormat,
  )
  final DateTime? startDate;

  /// The date when the schooling program was completed or
  /// is expected to be completed.
  /// This value can be null if the graduation date is not yet determined.
  @JsonKey(
    name: 'graduation_date',
    fromJson: _dateTimeFromCustomFormat,
    toJson: _dateTimeToCustomFormat,
  )
  final DateTime? graduationDate;

  /// The average grade obtained by the student across all subjects.
  @JsonKey(name: 'average_grade')
  final int averageGrade;

  /// The average grade required to pass or be considered approved.
  @JsonKey(name: 'average_approved_grade')
  final int averageApprovedGrade;

  /// The total number of subjects required to complete the schooling program.
  @JsonKey(name: 'subjects_required')
  final int subjectsRequired;

  /// The total number of subjects successfully completed by the student.
  @JsonKey(name: 'subjects_obtained')
  final int subjectsObtained;

  /// The total number of subjects failed by the student.
  @JsonKey(name: 'failed_subjects')
  final int failedSubjects;

  /// A list of subjects associated with the schooling program.
  final List<Subject> subjects;

  static DateTime? _dateTimeFromCustomFormat(String? date) {
    if (date == null || date.isEmpty) {
      return null;
    }
    return DateFormat('dd/MM/yyyy').parse(date);
  }

  static String? _dateTimeToCustomFormat(DateTime? date) {
    if (date == null) {
      return null;
    }
    return DateFormat('dd/MM/yyyy').format(date);
  }

  /// Creates a copy of the [Schooling] instance with the given fields replaced.
  Schooling copyWith({
    String? id,
    String? name,
    String? document,
    String? enrollmentNumber,
    String? title,
    String? plan,
    DateTime? startDate,
    DateTime? graduationDate,
    int? averageGrade,
    int? averageApprovedGrade,
    int? subjectsRequired,
    int? subjectsObtained,
    int? failedSubjects,
    List<Subject>? subjects,
  }) {
    return Schooling(
      id: id ?? this.id,
      name: name ?? this.name,
      document: document ?? this.document,
      enrollmentNumber: enrollmentNumber ?? this.enrollmentNumber,
      title: title ?? this.title,
      plan: plan ?? this.plan,
      startDate: startDate ?? this.startDate,
      graduationDate: graduationDate ?? this.graduationDate,
      averageGrade: averageGrade ?? this.averageGrade,
      averageApprovedGrade: averageApprovedGrade ?? this.averageApprovedGrade,
      subjectsRequired: subjectsRequired ?? this.subjectsRequired,
      subjectsObtained: subjectsObtained ?? this.subjectsObtained,
      failedSubjects: failedSubjects ?? this.failedSubjects,
      subjects: subjects ?? this.subjects,
    );
  }

  @override
  List<Object?> get props => [
        id,
        name,
        document,
        enrollmentNumber,
        title,
        plan,
        startDate,
        graduationDate,
        averageGrade,
        averageApprovedGrade,
        subjectsRequired,
        subjectsObtained,
        failedSubjects,
        subjects,
      ];
}
