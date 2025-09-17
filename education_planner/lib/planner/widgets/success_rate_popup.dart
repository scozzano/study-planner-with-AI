import 'package:flutter/material.dart';

class SuccessRatePopup extends StatefulWidget {
  const SuccessRatePopup({
    required this.successRate,
    required this.child,
    super.key,
  });

  final double successRate;
  final Widget child;

  @override
  State<SuccessRatePopup> createState() => _SuccessRatePopupState();
}

class _SuccessRatePopupState extends State<SuccessRatePopup>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _scaleAnimation;
  late Animation<double> _opacityAnimation;
  bool _isHovering = false;
  bool _hasShownInitially = false;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 200),
      vsync: this,
    );
    _scaleAnimation = Tween<double>(
      begin: 0,
      end: 1,
    ).animate(
      CurvedAnimation(
        parent: _animationController,
        curve: Curves.easeOutBack,
      ),
    );
    _opacityAnimation = Tween<double>(
      begin: 0,
      end: 1,
    ).animate(
      CurvedAnimation(
        parent: _animationController,
        curve: Curves.easeOut,
      ),
    );

    _showInitially();
  }

  void _showInitially() {
    Future.delayed(const Duration(milliseconds: 500), () {
      if (mounted && !_hasShownInitially) {
        _animationController.forward();
        _hasShownInitially = true;

        Future.delayed(const Duration(seconds: 3), () {
          if (mounted && !_isHovering) {
            _animationController.reverse();
          }
        });
      }
    });
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  void _onHoverEnter() {
    setState(() {
      _isHovering = true;
    });
    _animationController.forward();
  }

  void _onHoverExit() {
    setState(() {
      _isHovering = false;
    });
    if (_hasShownInitially) {
      _animationController.reverse();
    }
  }

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => _onHoverEnter(),
      onExit: (_) => _onHoverExit(),
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          widget.child,
          AnimatedBuilder(
            animation: _animationController,
            builder: (context, child) {
              if (_animationController.value > 0) {
                return Positioned(
                  top: -60,
                  left: 0,
                  right: 0,
                  child: Transform.scale(
                    scale: _scaleAnimation.value,
                    child: Opacity(
                      opacity: _opacityAnimation.value,
                      child: _SuccessRateBubble(
                        successRate: widget.successRate,
                      ),
                    ),
                  ),
                );
              }
              return const SizedBox.shrink();
            },
          ),
        ],
      ),
    );
  }
}

class _SuccessRateBubble extends StatelessWidget {
  const _SuccessRateBubble({
    required this.successRate,
  });

  final double successRate;

  @override
  Widget build(BuildContext context) {
    final percentage = (successRate * 100).toStringAsFixed(1);
    final color = _getSuccessRateColor(successRate);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.95),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.2),
            blurRadius: 8,
            offset: const Offset(0, 4),
          ),
        ],
        border: Border.all(
          color: color,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            _getSuccessRateIcon(successRate),
            size: 16,
            color: Colors.white,
          ),
          const SizedBox(width: 6),
          SizedBox(
            width: 100,
            child: Text(
              'Tu probabilidad de aprobar es $percentage%',
              maxLines: 4,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 12,
                fontWeight: FontWeight.w600,
                height: 1.3,
              ),
            ),
          ),
        ],
      ),
    );
  }

  IconData _getSuccessRateIcon(double rate) {
    if (rate >= 0.6) return Icons.trending_up;
    if (rate >= 0.5) return Icons.warning;
    return Icons.error;
  }

  Color _getSuccessRateColor(double rate) {
    if (rate >= 0.6) return const Color.fromARGB(255, 117, 154, 119);
    if (rate >= 0.5) return const Color.fromARGB(255, 217, 153, 75);
    return const Color.fromARGB(255, 250, 114, 112);
  }
}
