import 'package:equatable/equatable.dart';
import 'package:json_annotation/json_annotation.dart';

part 'pm_recommendation_models.g.dart';

@JsonSerializable(explicitToJson: true)

/// PM Algorithm Models - Simplified for recommendations only

class PMRecommendationResponse extends Equatable {
  /// Creates a new instance of [PMRecommendationResponse]
  const PMRecommendationResponse({
    required this.recommendations,
  });

  /// Creates a new instance of [PMRecommendationResponse] from a JSON object
  factory PMRecommendationResponse.fromJson(Map<String, dynamic> json) =>
      _$PMRecommendationResponseFromJson(json);

  /// Converts the [PMRecommendationResponse] instance to a JSON object
  Map<String, dynamic> toJson() => _$PMRecommendationResponseToJson(this);

  /// The recommendations
  final List<PMRecommendation> recommendations;

  @override
  List<Object?> get props => [recommendations];

  /// Returns only the subject IDs from the recommendations
  List<String> get subjectIds => recommendations.map((r) => r.subject).toList();
}

@JsonSerializable(explicitToJson: true)

/// PM Recommendation Model
class PMRecommendation extends Equatable {
  /// Creates a new instance of [PMRecommendation]
  const PMRecommendation({
    required this.subject,
    required this.score,
    required this.reason,
  });

  /// Creates a new instance of [PMRecommendation] from a JSON object
  factory PMRecommendation.fromJson(Map<String, dynamic> json) =>
      _$PMRecommendationFromJson(json);

  /// Converts the [PMRecommendation] instance to a JSON object
  Map<String, dynamic> toJson() => _$PMRecommendationToJson(this);

  /// The subject ID
  final String subject;

  /// The recommendation score
  final double score;

  /// The reason for the recommendation
  final String reason;

  @override
  List<Object?> get props => [subject, score, reason];

  /// Returns a formatted score
  String get formattedScore => score.toStringAsFixed(2);
}
