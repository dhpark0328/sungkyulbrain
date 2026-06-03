from __future__ import annotations
from .config import CONDUCTIVITY_WET_MAX, CONDUCTIVITY_FROZEN_MAX, CONDUCTIVITY_DRY_MAX

def infer_road_state(temperature_c: float, humidity_pct: float, frequency_hz: float) -> tuple[str, int, str]:
    conductivity = frequency_hz
    
    score = 0
    reasons = []

    # 1. Wet (주의) : 0 ~ CONDUCTIVITY_WET_MAX
    if 0 <= conductivity <= CONDUCTIVITY_WET_MAX:
        status = 'caution'
        score = 60
        reasons.append(f'전도도({conductivity}): Wet 구간 (젖은 노면) - 미끄럼 주의')
        
    # 2. Frozen (위험) : WET_MAX 초과 ~ FROZEN_MAX 이하
    elif CONDUCTIVITY_WET_MAX < conductivity <= CONDUCTIVITY_FROZEN_MAX:
        status = 'danger'
        score = 95
        reasons.append(f'전도도({conductivity}): Frozen 구간 (결빙) - 블랙아이스 위험')
        
    # 3. Dry (안전) : FROZEN_MAX 초과 ~ DRY_MAX 이하
    elif CONDUCTIVITY_FROZEN_MAX < conductivity <= CONDUCTIVITY_DRY_MAX:
        status = 'safe'
        score = 10
        reasons.append(f'전도도({conductivity}): Dry 구간 (건조) - 안전')
        
    # 예외 처리
    else:
        if conductivity > CONDUCTIVITY_DRY_MAX:
            status = 'safe'
            score = 5
            reasons.append(f'전도도({conductivity}): 매우 건조함 - 안전')
        else:
            status = 'unknown'
            score = 0
            reasons.append('측정값 오류')

    return status, score, ' / '.join(reasons)