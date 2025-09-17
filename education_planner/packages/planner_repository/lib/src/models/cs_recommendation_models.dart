import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';

part 'cs_recommendation_models.g.dart';

// Algorithm 3 - Success Probability
@JsonSerializable(explicitToJson: true)

/// Request model for Success Probability
class SuccessProbabilityRequest extends Equatable {
  /// Creates a new instance of [SuccessProbabilityRequest]
  const SuccessProbabilityRequest({
    required this.studentId,
    required this.candidateSubjects,
    required this.degreeYear,
  });

  /// Creates a new instance of [SuccessProbabilityRequest] from a JSON object
  factory SuccessProbabilityRequest.fromJson(Map<String, dynamic> json) =>
      _$SuccessProbabilityRequestFromJson(json);

  /// Converts the [SuccessProbabilityRequest] instance to a JSON object
  Map<String, dynamic> toJson() => _$SuccessProbabilityRequestToJson(this);

  /// The ID of the student
  @JsonKey(name: 'student_id')
  final int studentId;

  /// The candidate subjects
  @JsonKey(name: 'candidate_subjects')
  final List<String> candidateSubjects;

  /// The degree year
  @JsonKey(name: 'degree_year')
  final int degreeYear;

  @override
  List<Object?> get props => [studentId, candidateSubjects, degreeYear];
}

/// Response model for Success Probability
@JsonSerializable(explicitToJson: true)

/// Creates a new instance of [SuccessProbabilityResponse]
class SuccessProbabilityResponse extends Equatable {
  /// Creates a new instance of [SuccessProbabilityResponse]
  const SuccessProbabilityResponse({
    required this.recommendations,
  });

  /// Creates a new instance of [SuccessProbabilityResponse] from a JSON object
  factory SuccessProbabilityResponse.fromJson(Map<String, dynamic> json) =>
      _$SuccessProbabilityResponseFromJson(json);

  /// Converts the [SuccessProbabilityResponse] instance to a JSON object
  Map<String, dynamic> toJson() => _$SuccessProbabilityResponseToJson(this);

  /// The recommendations
  final List<SuccessRecommendation> recommendations;

  @override
  List<Object?> get props => [recommendations];
}

/// Model for a success recommendation
@JsonSerializable(explicitToJson: true)

/// Creates a new instance of [SuccessRecommendation]
class SuccessRecommendation extends Equatable {
  /// Creates a new instance of [SuccessRecommendation]
  const SuccessRecommendation({
    required this.subject,
    required this.pPass,
    required this.rank,
  });

  /// Creates a new instance of [SuccessRecommendation] from a JSON object
  factory SuccessRecommendation.fromJson(Map<String, dynamic> json) =>
      _$SuccessRecommendationFromJson(json);

  /// Converts the [SuccessRecommendation] instance to a JSON object
  Map<String, dynamic> toJson() => _$SuccessRecommendationToJson(this);

  /// The ID of the subject
  final String subject;

  /// The probability of passing the subject
  @JsonKey(name: 'p_pass')
  final double pPass;

  /// The rank of the subject
  final int rank;

  @override
  List<Object?> get props => [subject, pPass, rank];
}
