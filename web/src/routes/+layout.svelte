<script lang="ts">
    import type { Snippet } from "svelte";
import "./index.scss";

let {
    children,
}: {
    children?: Snippet,
} = $props();
</script>

{@render children?.()}