<script lang="ts">
    import type { LookupBreakdown } from "$lib/ploverApi";
    import {
        formatCost,
        formatEntryId,
        formatResultTitle,
        stepTransitions,
        transitionLabel,
    } from "./format";

    let {
        results,
    }: {
        results: LookupBreakdown[],
    } = $props();
</script>

<div class="result-list" aria-live="polite">
    {#each results as result}
        <article class="lookup-result">
            <header class="result-header">
                <div class="result-title">
                    <span>Translation</span>
                    <h2>{formatResultTitle(result)}</h2>
                </div>

                <div class="result-metadata">
                    <span>
                        <small>Entry</small>
                        <strong>{formatEntryId(result)}</strong>
                    </span>

                    <span>
                        <small>Cost</small>
                        <strong>{formatCost(result.cost)}</strong>
                    </span>
                </div>
            </header>

            {#if result.path.length > 0}
                <ol class="path-timeline">
                    {#each result.path as step, stepIndex}
                        {#if stepIndex > 0 && step.starts_new_stroke === true}
                            <li class="stroke-break" aria-label="Stroke break">/</li>
                        {/if}

                        <li class="path-step">
                            <div class="step-main">
                                <code>{step.chord}</code>

                                <div class="symbol-list">
                                    {#each step.theory_symbols as theorySymbol}
                                        <span>{theorySymbol}</span>
                                    {/each}
                                </div>
                            </div>

                            <div class="node-path">
                                {step.nodes.join(" -> ")}
                            </div>

                            {#if stepTransitions(step).length > 0}
                                <div class="transition-list">
                                    {#each stepTransitions(step) as transition}
                                        <span title={transitionLabel(transition)}>
                                            <strong>{transition.key}</strong>
                                            <small>{formatCost(transition.cost)}</small>
                                        </span>
                                    {/each}
                                </div>
                            {/if}
                        </li>
                    {/each}
                </ol>
            {:else}
                <div class="message compact">No path data</div>
            {/if}
        </article>
    {/each}
</div>

<style lang="scss">
    .result-list {
        display: grid;
        align-content: start;
        gap: 0.8rem;

        height: 100%;
        min-width: 0;
        min-height: 0;
        overflow: auto;
        padding-right: 0.2rem;
    }

    .lookup-result {
        display: grid;
        gap: 0.8rem;

        min-width: 0;
        padding: 0.85rem;
        border: 0.0625rem solid oklch(0.84 0.016 155);
        border-radius: 0.5rem;
        background: oklch(0.99 0.003 155);
    }

    .result-header {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: center;
        gap: 0.75rem;

        min-width: 0;
    }

    .result-title {
        display: grid;
        gap: 0.18rem;

        min-width: 0;
    }

    .result-title span {
        color: oklch(0.43 0.035 170);
        font-size: 0.72rem;
        font-weight: 780;
        letter-spacing: 0;
        text-transform: uppercase;
    }

    h2 {
        min-width: 0;
        overflow: hidden;
        margin: 0;
        color: oklch(0.2 0.028 160);
        font-size: 1.05rem;
        font-weight: 780;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .result-metadata {
        display: flex;
        align-items: center;
        gap: 0.45rem;

        min-width: 0;
    }

    .result-metadata span {
        display: grid;
        gap: 0.08rem;

        min-width: 4.4rem;
        padding: 0.28rem 0.45rem;
        border: 0.0625rem solid oklch(0.78 0.04 220);
        border-radius: 0.375rem;
        background: oklch(0.97 0.018 220);
        color: oklch(0.28 0.055 220);
    }

    .result-metadata small {
        font-size: 0.68rem;
        font-weight: 760;
        text-transform: uppercase;
    }

    .result-metadata strong {
        font-size: 0.88rem;
        font-weight: 800;
    }

    .path-timeline {
        display: grid;
        gap: 0.65rem;

        min-width: 0;
        margin: 0;
        padding: 0;
        list-style: none;
    }

    .path-step {
        display: grid;
        grid-template-columns: minmax(9rem, 0.45fr) minmax(7rem, 0.28fr) minmax(10rem, 0.45fr);
        align-items: center;
        gap: 0.75rem;

        min-width: 0;
        padding: 0.65rem 0;
        border-top: 0.0625rem solid oklch(0.89 0.012 160);
    }

    .path-step:first-child {
        border-top: 0;
    }

    .step-main,
    .symbol-list,
    .transition-list {
        display: flex;
        align-items: center;
        gap: 0.45rem;

        min-width: 0;
    }

    .step-main,
    .symbol-list,
    .transition-list {
        flex-wrap: wrap;
    }

    code {
        min-width: 3.6rem;
        padding: 0.22rem 0.45rem;
        border-radius: 0.25rem;
        background: oklch(0.22 0.03 165);
        color: oklch(0.98 0.004 160);
        font-family: "Atkinson Hyperlegible Mono", monospace;
        font-size: 0.9rem;
        font-weight: 760;
        text-align: center;
    }

    .symbol-list span {
        padding: 0.12rem 0.4rem;
        border: 0.0625rem solid oklch(0.75 0.07 70);
        border-radius: 999rem;
        background: oklch(0.96 0.04 80);
        color: oklch(0.34 0.08 75);
        font-size: 0.78rem;
        font-weight: 780;
    }

    .node-path {
        min-width: 0;
        overflow: hidden;
        color: oklch(0.38 0.03 165);
        font-family: "Atkinson Hyperlegible Mono", monospace;
        font-size: 0.78rem;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .transition-list {
        justify-content: flex-end;
    }

    .transition-list span {
        display: inline-flex;
        align-items: baseline;
        gap: 0.32rem;

        min-width: 0;
        padding: 0.14rem 0.4rem;
        border: 0.0625rem solid oklch(0.76 0.04 220);
        border-radius: 0.25rem;
        background: oklch(0.97 0.018 220);
        color: oklch(0.28 0.055 220);
    }

    .transition-list strong {
        font-size: 0.8rem;
        font-weight: 780;
    }

    .transition-list small {
        color: oklch(0.42 0.04 220);
        font-size: 0.72rem;
        font-weight: 720;
    }

    .stroke-break {
        display: grid;
        place-items: center;

        min-height: 1.2rem;
        color: oklch(0.45 0.035 170);
        font-family: "Atkinson Hyperlegible Mono", monospace;
        font-size: 1.2rem;
        font-weight: 780;
    }

    .message {
        min-height: 2rem;
        align-self: start;
        padding: 0.45rem 0.65rem;
        border: 0.0625rem solid oklch(0.84 0.018 155);
        border-radius: 0.375rem;
        background: oklch(0.97 0.008 155);
        color: oklch(0.36 0.025 160);
        font-size: 0.84rem;
    }

    @media (max-width: 58rem) {
        .path-step {
            grid-template-columns: 1fr;
            gap: 0.45rem;
        }

        .transition-list {
            justify-content: flex-start;
        }
    }

    @media (max-width: 48rem) {
        .result-header {
            grid-template-columns: 1fr;
            gap: 0.35rem;
        }

        .result-metadata {
            flex-wrap: wrap;
        }

        h2 {
            white-space: normal;
        }
    }
</style>
