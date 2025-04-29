import {exists} from "jsr:@std/fs/exists";
import {parse} from "jsr:@eemeli/yaml";


if (await exists("./out")) {
    await Deno.remove("./out", {recursive: true});
}
await Deno.mkdir("./out", {recursive: true});

for await (const file of Deno.readDir("./syntaxes")) {
    if (!file.isFile) continue;
    if (!file.name.endsWith(".yaml")) continue;

    const grammarYaml = new TextDecoder().decode(await Deno.readFile(`./syntaxes/${file.name}`));
    const grammar = parse(grammarYaml);
    const grammarJson = JSON.stringify(grammar);
    await Deno.writeFile(
        `./out/${file.name.slice(0, file.name.lastIndexOf("."))}.json`,
        new TextEncoder().encode(grammarJson),
        {create: true},
    );
}
