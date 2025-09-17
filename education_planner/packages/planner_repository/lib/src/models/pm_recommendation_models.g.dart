// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pm_recommendation_models.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PMRecommendationResponse _$PMRecommendationResponseFromJson(
  Map<String, dynamic> json,
) =>
    PMRecommendationResponse(
      recommendations: (json['recommendations'] as List<dynamic>)
          .map((e) => PMRecommendation.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$PMRecommendationResponseToJson(
  PMRecommendationResponse instance,
) =>
    <String, dynamic>{
      'recommendations':
          instance.recommendations.map((e) => e.toJson()).toList(),
    };

PMRecommendation _$PMRecommendationFromJson(Map<String, dynamic> json) =>
    PMRecommendation(
      subject: json['subject'] as String,
      score: (json['score'] as num).toDouble(),
      reason: json['reason'] as String,
    );

Map<String, dynamic> _$PMRecommendationToJson(PMRecommendation instance) =>
    <String, dynamic>{
      'subject': instance.subject,
      'score': instance.score,
      'reason': instance.reason,
    };
