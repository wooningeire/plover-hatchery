export const LINK_ARC = 0.5;

export const linkPathSegment = (x1: number, y1: number, x2: number, y2: number) => {
    const dx = x2 - x1;
    const arcHeight = -dx * LINK_ARC;
    
    const cp1x = x1 + dx / 4;
    const cp1y = y1 + arcHeight;
    
    const cp2x = x2 - dx / 4;
    const cp2y = y2 + arcHeight;
    
    return `M${x1},${y1} C${cp1x},${cp1y} ${cp2x},${cp2y} ${x2},${y2}`;
};

export const linkPathYMax = (x1: number, y1: number, x2: number, y2: number) => {
    const dx = x2 - x1;
    const arcHeight = -dx * LINK_ARC;
    
    return y1 + arcHeight * 0.75;
};