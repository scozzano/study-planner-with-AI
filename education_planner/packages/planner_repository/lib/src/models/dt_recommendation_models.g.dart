// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'dt_recommendation_models.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DecisionTreeResponse _$DecisionTreeResponseFromJson(
  Map<String, dynamic> json,
) =>
    DecisionTreeResponse(
      scoreDict: (json['score_dict'] as Map<String, dynamic>?)?.map(
        (k, e) =>
            MapEntry(k, DecisionTreeScore.fromJson(e as Map<String, dynamic>)),
      ),
      dtNames: (json['DT_names'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList(),
      figures:
          (json['figures'] as List<dynamic>?)?.map((e) => e as String).toList(),
      parsed: json['parsed'] as List<dynamic>?,
      errorMsg: json['error_msg'] as String?,
    );

Map<String, dynamic> _$DecisionTreeResponseToJson(
  DecisionTreeResponse instance,
) =>
    <String, dynamic>{
      'score_dict': instance.scoreDict?.map((k, e) => MapEntry(k, e.toJson())),
      'DT_names': instance.dtNames,
      'figures': instance.figures,
      'parsed': instance.parsed,
      'error_msg': instance.errorMsg,
    };

DecisionTreeScore _$DecisionTreeScoreFromJson(Map<String, dynamic> json) =>
    DecisionTreeScore(
      classMetrics: (json['classMetrics'] as Map<String, dynamic>?)?.map(
        (k, e) => MapEntry(k, ClassMetrics.fromJson(e as Map<String, dynamic>)),
      ),
      accuracy: (json['accuracy'] as List<dynamic>?)
          ?.map((e) => (e as num).toDouble())
          .toList(),
    );

Map<String, dynamic> _$DecisionTreeScoreToJson(DecisionTreeScore instance) =>
    <String, dynamic>{
      'classMetrics':
          instance.classMetrics?.map((k, e) => MapEntry(k, e.toJson())),
      'accuracy': instance.accuracy,
    };

ClassMetrics _$ClassMetricsFromJson(Map<String, dynamic> json) => ClassMetrics(
      precision: (json['precision'] as List<dynamic>?)
          ?.map((e) => (e as num).toDouble())
          .toList(),
      recall: (json['recall'] as List<dynamic>?)
          ?.map((e) => (e as num).toDouble())
          .toList(),
    );

Map<String, dynamic> _$ClassMetricsToJson(ClassMetrics instance) =>
    <String, dynamic>{
      'precision': instance.precision,
      'recall': instance.recall,
    };

DecisionTreeRule _$DecisionTreeRuleFromJson(Map<String, dynamic> json) =>
    DecisionTreeRule(
      condition: json['condition'] as String,
      samples: (json['samples'] as num).toInt(),
      value: (json['value'] as num).toDouble(),
      impurity: (json['impurity'] as num).toDouble(),
      classDistribution: json['classDistribution'] as List<dynamic>?,
    );

Map<String, dynamic> _$DecisionTreeRuleToJson(DecisionTreeRule instance) =>
    <String, dynamic>{
      'condition': instance.condition,
      'samples': instance.samples,
      'value': instance.value,
      'impurity': instance.impurity,
      'classDistribution': instance.classDistribution,
    };
