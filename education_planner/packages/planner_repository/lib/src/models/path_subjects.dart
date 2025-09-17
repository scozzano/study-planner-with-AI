import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';

part 'path_subjects.g.dart';

/// Converts string to int for id field validation
int? stringToInt(dynamic json) {
  if (json == null) return null;
  if (json is int) return json;
  if (json is String) {
    return int.tryParse(json);
  }
  return null;
}

/// Converts int to dynamic for JSON serialization
dynamic intToString(int? object) => object;

@JsonSerializable()

/// {@template path_subject}
/// A model representing a subject in a path.
/// This class is used to
/// represent a subject in a path.
/// It contains the subject's
/// id, name, and semester.
/// {@endtemplate}
class PathSubject extends Equatable {
  /// {@macro path_subject}
  const PathSubject({
    required this.id,
    required this.name,
    this.semester = 0,
    this.subjectIds = const [],
    this.status = '',
    this.isRecommended = false,
    this.isRecommendationAccepted = false,
    this.suggestedSemester = 0,
    this.successRate = 0.0,
  });

  /// Creates a new instance of [PathSubject] from a JSON object.
  factory PathSubject.fromJson(Map<String, dynamic> json) =>
      _$PathSubjectFromJson(json);

  /// The id of the subject.
  @JsonKey(fromJson: stringToInt, toJson: intToString)
  final int? id;

  /// The name of the subject.
  final String name;

  /// The semester of the subject.
  final double semester;

  /// The status of the subject, if applicable.
  final String? status;

  /// The list of subject ids that this elective subject has to choose from.
  final List<int> subjectIds;

  /// Checks if the subject is approved.
  bool get isApproved => status == 'APR';

  /// Whether the subject is recommended.
  @JsonKey(includeFromJson: false, includeToJson: false)
  final bool isRecommended;

  /// Whether the subject recommendation has been accepted.
  @JsonKey(includeFromJson: false, includeToJson: false)
  final bool isRecommendationAccepted;

  /// The semester suggested for the subject.
  @JsonKey(includeFromJson: false, includeToJson: false)
  final double suggestedSemester;

  /// The success rate for the subject recommendation (0.0 to 1.0).
  @JsonKey(includeFromJson: false, includeToJson: false)
  final double successRate;

  /// Returns the success rate as a percentage string.
  String get successRatePercentage =>
      '${(successRate * 100).toStringAsFixed(1)}%';

  /// Converts the [PathSubject] instance to a JSON object.
  Map<String, dynamic> toJson() => _$PathSubjectToJson(this);

  /// Creates a copy of the [PathSubject] instance with optional new values.
  PathSubject copyWith({
    int? id,
    String? name,
    double? semester,
    List<int>? subjectIds,
    String? status,
    bool? isRecommended,
    bool? isRecommendationAccepted,
    double? suggestedSemester,
    double? successRate,
  }) {
    return PathSubject(
      id: id ?? this.id,
      name: name ?? this.name,
      semester: semester ?? this.semester,
      subjectIds: subjectIds ?? this.subjectIds,
      status: status ?? this.status,
      isRecommended: isRecommended ?? this.isRecommended,
      isRecommendationAccepted:
          isRecommendationAccepted ?? this.isRecommendationAccepted,
      suggestedSemester: suggestedSemester ?? this.suggestedSemester,
      successRate: successRate ?? this.successRate,
    );
  }

  @override
  List<Object?> get props => [
        id,
        name,
        semester,
        subjectIds,
        status,
        isApproved,
        isRecommended,
        isRecommendationAccepted,
        suggestedSemester,
        successRate,
      ];
}
