<script lang="ts">
    interface Props {
        flags: string[];
        opacities: Record<string, number>;
    }

    let { flags, opacities = $bindable() }: Props = $props();
</script>

<div class="controls">
    <h3>Transition Flags</h3>
    {#if flags.length === 0}
        <div class="empty">No flags found</div>
    {/if}
    {#each flags as flag}
        <div class="flag-control">
            <span class="flag-name">{flag}</span>
            <input 
                type="range" 
                min="0" 
                max="1" 
                step="0.1" 
                bind:value={opacities[flag]} 
            />
            <span class="value">{opacities[flag]}</span>
        </div>
    {/each}
</div>

<style>
    .controls {
        margin-bottom: 1rem;
        padding: 1rem;
        background: #f9f9f9;
        border: 1px solid #eee;
        border-radius: 4px;
        max-height: 200px;
        overflow-y: auto;
    }
    .flag-control {
        display: grid;
        grid-template-columns: 150px 1fr 40px;
        gap: 1rem;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    .flag-name {
        font-weight: 600;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .value {
        text-align: right;
        font-variant-numeric: tabular-nums;
        color: #666;
    }
    input[type="range"] {
        width: 100%;
        cursor: pointer;
    }
    .empty {
        color: #666;
        font-style: italic;
    }
</style>
