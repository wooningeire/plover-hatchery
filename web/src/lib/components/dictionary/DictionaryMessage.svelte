<script lang="ts">
    import type { Snippet } from "svelte";

    type MessageVariant = "neutral" | "success" | "error";
    type LiveMode = "off" | "polite" | "assertive";

    let {
        variant = "neutral",
        compact = false,
        live,
        children,
    }: {
        variant?: MessageVariant,
        compact?: boolean,
        live?: LiveMode,
        children?: Snippet,
    } = $props();
</script>

<div
    class="message"
    class:compact
    class:is-success={variant === "success"}
    class:is-error={variant === "error"}
    aria-live={live}
>
    {@render children?.()}
</div>

<style lang="scss">
    @use "./dictionaryUi.scss" as ui;

    .message {
        @include ui.message;
    }

    .message.compact {
        min-height: 2.125rem;
        font-size: 0.86rem;
    }

    .message.is-success {
        @include ui.success-message;
    }

    .message.is-error {
        @include ui.error-message;
    }

    .message :global(a) {
        color: currentColor;
        font-weight: 760;
    }

    @media (max-width: 42rem) {
        .message {
            align-items: flex-start;
            flex-direction: column;
        }
    }
</style>
