import 'package:education_planner/planner/widgets/success_rate_popup.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:planner_repository/planner_repository.dart';

class PlanCard extends StatefulWidget {
  const PlanCard({required this.subject, super.key});

  final PathSubject subject;

  @override
  State<PlanCard> createState() => _PlanCardState();
}

class _PlanCardState extends State<PlanCard> {
  @override
  Widget build(BuildContext context) {
    final cardWidget = Card(
      color: widget.subject.isRecommended
          ? const Color.fromARGB(255, 185, 158, 231)
          : widget.subject.isApproved
              ? const Color.fromARGB(255, 175, 194, 179)
              : Theme.of(context).colorScheme.primaryContainer,
      elevation: 2,
      child: Stack(
        children: [
          Center(
            child: SizedBox(
              height: 100,
              width: 150,
              child: Center(
                child: SizedBox(
                  width: 100,
                  child: Text(
                    widget.subject.name,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ),
              ),
            ),
          ),
          if (widget.subject.isRecommended)
            const Positioned(
              bottom: 0,
              right: 0,
              child: Padding(
                padding: EdgeInsets.all(12),
                child: Icon(
                  CupertinoIcons.sparkles,
                  size: 12,
                  color: Color.fromARGB(255, 21, 37, 24),
                ),
              ),
            ),
          if (widget.subject.isApproved)
            const Positioned(
              bottom: 0,
              right: 0,
              child: Padding(
                padding: EdgeInsets.all(12),
                child: Icon(
                  Icons.check,
                  size: 12,
                  color: Color.fromARGB(255, 21, 37, 24),
                ),
              ),
            ),
        ],
      ),
    );

    // Show popup if subject is recommended and has success rate data
    if (widget.subject.successRate > 0) {
      return SuccessRatePopup(
        successRate: widget.subject.successRate,
        child: cardWidget,
      );
    }

    return cardWidget;
  }
}

class ShinyBorderPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    // Create a static shiny gradient with multiple colors
    final paint = Paint()
      ..shader = LinearGradient(
        colors: [
          const Color.fromARGB(255, 215, 234, 188).withValues(alpha: 1),
          const Color.fromARGB(255, 78, 203, 189).withValues(alpha: 0.8),
          const Color.fromARGB(255, 202, 250, 255).withValues(alpha: 0.9),
          const Color.fromARGB(255, 113, 180, 149).withValues(alpha: 1),
        ],
        stops: const [0.0, 0.33, 0.66, 1.0],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height))
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.0
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4);

    // Draw the main shiny border
    final rect = RRect.fromRectAndRadius(
      Rect.fromLTWH(2, 2, size.width - 4, size.height - 4),
      const Radius.circular(12),
    );
    canvas.drawRRect(rect, paint);

    // Draw a secondary inner border for extra shine
    final innerPaint = Paint()
      ..shader = LinearGradient(
        colors: [
          Colors.white.withValues(alpha: 0.8),
          Colors.cyan.withValues(alpha: 0.6),
          Colors.white.withValues(alpha: 0.8),
        ],
        stops: const [0.0, 0.5, 1.0],
        begin: Alignment.topRight,
        end: Alignment.bottomLeft,
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height))
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 2);

    final innerRect = RRect.fromRectAndRadius(
      Rect.fromLTWH(4, 4, size.width - 8, size.height - 8),
      const Radius.circular(10),
    );
    canvas.drawRRect(innerRect, innerPaint);

    // Draw outer glow for enhanced effect
    final outerPaint = Paint()
      ..shader = RadialGradient(
        colors: [
          Colors.purple.withValues(alpha: 0.4),
          Colors.blue.withValues(alpha: 0.2),
          Colors.transparent,
        ],
        stops: const [0.0, 0.7, 1.0],
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height))
      ..style = PaintingStyle.stroke
      ..strokeWidth = 6.0
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 8);

    final outerRect = RRect.fromRectAndRadius(
      Rect.fromLTWH(-1, -1, size.width + 2, size.height + 2),
      const Radius.circular(14),
    );
    canvas.drawRRect(outerRect, outerPaint);
  }

  @override
  bool shouldRepaint(ShinyBorderPainter oldDelegate) => false;
}
