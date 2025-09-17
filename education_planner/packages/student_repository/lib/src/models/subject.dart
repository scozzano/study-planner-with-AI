import 'package:equatable/equatable.dart';
import 'package:intl/intl.dart';
import 'package:json_annotation/json_annotation.dart';

part 'subject.g.dart';

@JsonSerializable()

/// Represents a subject in a student's schooling record.
class Subject extends Equatable {
  /// Creates a new instance of [Subject].
  const Subject({
    required this.code,
    required this.name,
    required this.semester,
    required this.date,
    required this.status,
    required this.grade,
    this.attempts = 0,
    this.lastAttemptDate,
    this.resultType,
  });

  /// Creates a new instance of [Subject] from a JSON map.
  factory Subject.fromJson(Map<String, dynamic> json) =>
      _$SubjectFromJson(json);

  /// Converts the [Subject] instance to a JSON map.
  Map<String, dynamic> toJson() => _$SubjectToJson(this);

  /// The unique code identifying the subject.
  final String code;

  /// The name of the subject.
  final String name;

  /// The semester in which the subject is offered.
  final String semester;

  /// The date associated with the subject, such as
  ///  the enrollment or start date.
  @JsonKey(
    fromJson: _dateTimeFromCustomFormat,
    toJson: _dateTimeToCustomFormat,
  )
  final DateTime? date;

  /// The current status of the subject (e.g., "completed", "in progress").
  final String status;

  /// The grade achieved in the subject.
  final int? grade;

  /// The number of attempts made for the subject, if applicable.
  final int? attempts;

  /// The date of the last attempt for the subject, if applicable.
  @JsonKey(
    name: 'last_attempt_date',
    fromJson: _dateTimeFromCustomFormat,
    toJson: _dateTimeToCustomFormat,
  )
  final DateTime? lastAttemptDate;

  /// The type of result for the subject, if applicable.
  @JsonKey(name: 'result_type')
  final String? resultType;

  /// Checks if the subject is approved based on the status.
  bool get isApproved =>
      status == 'APR' && (resultType == null || resultType == 'T');

  /// Checks if the subject is a total credit subject.
  bool get isTotalCredit => resultType == 'T';

  static DateTime? _dateTimeFromCustomFormat(String? date) {
    if (date == null) {
      return null;
    }
    return DateFormat('yyyy-MM-dd').tryParse(date) ??
        DateFormat('dd/MM/yyyy').parse(date);
  }

  static String? _dateTimeToCustomFormat(DateTime? date) {
    if (date == null) {
      return null;
    }
    return DateFormat('yyyy-MM-dd').format(date);
  }

  @override
  List<Object?> get props => [
        code,
        name,
        semester,
        date,
        status,
        grade,
        attempts,
        lastAttemptDate,
        resultType,
      ];
}
