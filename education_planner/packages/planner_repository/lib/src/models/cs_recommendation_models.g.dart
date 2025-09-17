// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'cs_recommendation_models.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SuccessProbabilityRequest _$SuccessProbabilityRequestFromJson(
  Map<String, dynamic> json,
) =>
    SuccessProbabilityRequest(
      studentId: (json['student_id'] as num).toInt(),
      candidateSubjects: (json['candidate_subjects'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      degreeYear: (json['degree_year'] as num).toInt(),
    );

Map<String, dynamic> _$SuccessProbabilityRequestToJson(
  SuccessProbabilityRequest instance,
) =>
    <String, dynamic>{
      'student_id': instance.studentId,
      'candidate_subjects': instance.candidateSubjects,
      'degree_year': instance.degreeYear,
    };

SuccessProbabilityResponse _$SuccessProbabilityResponseFromJson(
  Map<String, dynamic> json,
) =>
    SuccessProbabilityResponse(
      recommendations: (json['recommendations'] as List<dynamic>)
          .map((e) => SuccessRecommendation.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$SuccessProbabilityResponseToJson(
  SuccessProbabilityResponse instance,
) =>
    <String, dynamic>{
      'recommendations':
          instance.recommendations.map((e) => e.toJson()).toList(),
    };

SuccessRecommendation _$SuccessRecommendationFromJson(
  Map<String, dynamic> json,
) =>
    SuccessRecommendation(
      subject: json['subject'] as String,
      pPass: (json['p_pass'] as num).toDouble(),
      rank: (json['rank'] as num).toInt(),
    );

Map<String, dynamic> _$SuccessRecommendationToJson(
  SuccessRecommendation instance,
) =>
    <String, dynamic>{
      'subject': instance.subject,
      'p_pass': instance.pPass,
      'rank': instance.rank,
    };
