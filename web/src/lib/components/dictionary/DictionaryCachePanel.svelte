<script lang="ts">
    import DictionaryMessage from "./DictionaryMessage.svelte";
    import type {
        CompileAction,
        CompileState,
    } from "./types";

    let {
        compileAction,
        compileState,
        compileError,
        compiledDictionaryCount,
        compileIsWorking,
        onCompile,
    }: {
        compileAction: CompileAction,
        compileState: CompileState,
        compileError: string | null,
        compiledDictionaryCount: number,
        compileIsWorking: boolean,
        onCompile: (refreshCache: boolean) => void | Promise<void>,
    } = $props();
</script>

<section class="cache-panel" aria-labelledby="cache-title">
    <div>
        <p class="eyebrow">Cache</p>
        <h2 id="cache-title">Manual cache management</h2>
    </div>

    <div class="button-row">
        <button
            type="button"
            class="button"
            class:is-working={compileIsWorking && compileAction === "compile"}
            disabled={compileIsWorking}
            onclick={() => void onCompile(false)}
        >
            {compileIsWorking && compileAction === "compile" ? "Compiling" : "Compile"}
        </button>

        <button
            type="button"
            class="button secondary"
            class:is-working={compileIsWorking && compileAction === "refresh"}
            disabled={compileIsWorking}
            onclick={() => void onCompile(true)}
        >
            {compileIsWorking && compileAction === "refresh" ? "Refreshing" : "Refresh cache"}
        </button>
    </div>

    <DictionaryMessage
        compact
        live="polite"
        variant={compileState === "compiled" ? "success" : compileState === "error" ? "error" : "neutral"}
    >
        {#if compileState === "idle"}
            Ready
        {:else if compileState === "compiling"}
            {compileAction === "refresh" ? "Refreshing cache" : "Compiling theory"}
        {:else if compileState === "compiled"}
            Compiled {compiledDictionaryCount} {compiledDictionaryCount === 1 ? "dictionary" : "dictionaries"}
        {:else}
            {compileError ?? "Compile failed"}
        {/if}
    </DictionaryMessage>
</section>

<style lang="scss">
    @use "./dictionaryUi.scss" as ui;

    .cache-panel {
        @include ui.panel-surface;

        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 1rem;

        min-width: 0;
        padding: 1rem;
    }

    .cache-panel :global(.message) {
        grid-column: 1 / -1;
    }

    .eyebrow {
        @include ui.eyebrow;
    }

    h2 {
        @include ui.h2;
    }

    .button-row {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        justify-content: flex-end;
        gap: 0.75rem;
    }

    .button {
        @include ui.button;
        @include ui.secondary-button;
    }

    @media (max-width: 58rem) {
        .cache-panel {
            grid-template-columns: 1fr;
        }

        .button-row {
            justify-content: stretch;
        }

        .button-row .button {
            width: 100%;
        }
    }
</style>
