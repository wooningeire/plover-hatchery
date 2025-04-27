import {parse} from "@eemeli/yaml";

const grammarYaml = new TextDecoder().decode(await Deno.readFile("./syntaxes/hatchery.tmLanguage.yaml"));
const grammar = parse(grammarYaml);
const grammarJson = JSON.stringify(grammar);
await Deno.writeFile("./out/hatchery.tmLanguage.json", new TextEncoder().encode(grammarJson));

