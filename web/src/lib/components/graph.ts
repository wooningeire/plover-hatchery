export const LINK_ARC = 0.5;

export type GraphNodeXOptions = {
    index: number,
    paddingX: number,
    nodeSpacing: number,
    spacingScale: number,
};

export type GraphViewBoxWidthOptions = {
    nodeCount: number,
    paddingX: number,
    nodeSpacing: number,
    spacingScale: number,
    minWidth: number,
};

export const clampSpacingScale = (spacingScale: number) => {
    if (!Number.isFinite(spacingScale)) {
        return 1;
    }

    return Math.min(1, Math.max(0, spacingScale));
};

export const scaledNodeSpacing = (nodeSpacing: number, spacingScale: number) => (
    nodeSpacing * clampSpacingScale(spacingScale)
);

export const graphNodeX = ({
    index,
    paddingX,
    nodeSpacing,
    spacingScale,
}: GraphNodeXOptions) => (
    paddingX + index * scaledNodeSpacing(nodeSpacing, spacingScale)
);

export const graphViewBoxWidth = ({
    nodeCount,
    paddingX,
    nodeSpacing,
    spacingScale,
    minWidth,
}: GraphViewBoxWidthOptions) => (
    Math.max(
        minWidth,
        Math.max(1, nodeCount - 1) * scaledNodeSpacing(nodeSpacing, spacingScale) + paddingX * 2,
    )
);

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
