using System.Xml;
using System.Xml.Linq;

namespace AccessibleMediaController.Core.Devices.FrontierSmart;

public static class FrontierSmartXmlParser
{
    private const int MaximumXmlCharacters = 1024 * 1024;

    public static FrontierSmartValue ParseValue(string node, string xml)
    {
        var document = ParseDocument(xml);
        var response = RequireElement(document.Root, "fsapiResponse");
        return ParseValueElement(node, response);
    }

    public static IReadOnlyDictionary<string, FrontierSmartValue> ParseMultiple(string xml)
    {
        var document = ParseDocument(xml);
        var root = RequireElement(document.Root, "fsapiGetMultipleResponse");
        var values = new Dictionary<string, FrontierSmartValue>(StringComparer.Ordinal);
        foreach (var response in Children(root, "fsapiResponse"))
        {
            var node = ChildValue(response, "node")?.Trim();
            if (string.IsNullOrWhiteSpace(node))
                throw new FormatException("Odpowiedź GET_MULTIPLE nie zawiera nazwy węzła.");
            values[node] = ParseValueElement(node, response);
        }
        return values;
    }

    public static IReadOnlyList<FrontierSmartMode> ParseModes(string xml)
    {
        var (status, items) = ParseList(xml);
        EnsureSuccess(status, "Nie udało się odczytać trybów urządzenia Frontier Smart.");
        return items.Select(item => new FrontierSmartMode(
                item.Key,
                item.Field("id") ?? string.Empty,
                item.Field("label") ?? item.Field("id") ?? $"Tryb {item.Key + 1}",
                item.FieldBoolean("selectable") ?? false,
                item.FieldBoolean("streamable") ?? false,
                item.FieldUInt32("modetype") ?? 0))
            .ToArray();
    }

    public static IReadOnlyList<FrontierSmartPreset> ParsePresets(string xml)
    {
        var (status, items) = ParseList(xml);
        EnsureSuccess(status, "Nie udało się odczytać presetów urządzenia Frontier Smart.");
        return items.Select(item => new FrontierSmartPreset(
                item.Key,
                item.Field("name") ?? $"Preset {item.Key + 1}"))
            .ToArray();
    }

    public static string ParseStatus(string xml)
    {
        var document = ParseDocument(xml);
        var response = RequireElement(document.Root, "fsapiResponse");
        return ChildValue(response, "status")?.Trim()
            ?? throw new FormatException("Odpowiedź FSAPI nie zawiera statusu.");
    }

    private static (string Status, IReadOnlyList<ListItem> Items) ParseList(string xml)
    {
        var document = ParseDocument(xml);
        var response = RequireElement(document.Root, "fsapiResponse");
        var status = ChildValue(response, "status")?.Trim()
            ?? throw new FormatException("Odpowiedź listy FSAPI nie zawiera statusu.");
        var items = Children(response, "item")
            .Select(ParseListItem)
            .ToArray();
        return (status, items);
    }

    private static ListItem ParseListItem(XElement element)
    {
        var keyText = element.Attribute("key")?.Value;
        if (!uint.TryParse(keyText, out var key))
            throw new FormatException("Element listy FSAPI nie zawiera poprawnego klucza.");
        var fields = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (var field in Children(element, "field"))
        {
            var name = field.Attribute("name")?.Value;
            if (string.IsNullOrWhiteSpace(name)) continue;
            fields[name] = field.Elements().FirstOrDefault()?.Value.Trim()
                ?? field.Value.Trim();
        }
        return new ListItem(key, fields);
    }

    private static FrontierSmartValue ParseValueElement(string node, XElement response)
    {
        var status = ChildValue(response, "status")?.Trim()
            ?? throw new FormatException("Odpowiedź FSAPI nie zawiera statusu.");
        var valueElement = Child(response, "value");
        var typedValue = valueElement?.Elements().FirstOrDefault();
        return new FrontierSmartValue(
            node,
            status,
            typedValue?.Name.LocalName,
            typedValue?.Value.Trim());
    }

    private static XDocument ParseDocument(string xml)
    {
        if (string.IsNullOrWhiteSpace(xml))
            throw new FormatException("Urządzenie zwróciło pustą odpowiedź FSAPI.");
        if (xml.Length > MaximumXmlCharacters)
            throw new FormatException("Odpowiedź XML urządzenia jest zbyt duża.");

        var settings = new XmlReaderSettings
        {
            DtdProcessing = DtdProcessing.Prohibit,
            XmlResolver = null,
            MaxCharactersInDocument = MaximumXmlCharacters,
            IgnoreComments = true,
            IgnoreProcessingInstructions = true
        };
        using var stringReader = new StringReader(xml);
        using var reader = XmlReader.Create(stringReader, settings);
        return XDocument.Load(reader, LoadOptions.None);
    }

    private static XElement RequireElement(XElement? element, string localName)
    {
        if (element is null || !element.Name.LocalName.Equals(localName, StringComparison.Ordinal))
            throw new FormatException($"Nieoczekiwany główny element odpowiedzi FSAPI: oczekiwano {localName}.");
        return element;
    }

    private static XElement? Child(XElement element, string localName) =>
        element.Elements().FirstOrDefault(candidate =>
            candidate.Name.LocalName.Equals(localName, StringComparison.Ordinal));

    private static string? ChildValue(XElement element, string localName) =>
        Child(element, localName)?.Value;

    private static IEnumerable<XElement> Children(XElement element, string localName) =>
        element.Elements().Where(candidate =>
            candidate.Name.LocalName.Equals(localName, StringComparison.Ordinal));

    private static void EnsureSuccess(string status, string message)
    {
        if (!status.Equals("FS_OK", StringComparison.Ordinal))
            throw new FrontierSmartProtocolException(message, status);
    }

    private sealed record ListItem(uint Key, IReadOnlyDictionary<string, string> Fields)
    {
        public string? Field(string name) => Fields.GetValueOrDefault(name);

        public uint? FieldUInt32(string name) =>
            uint.TryParse(Field(name), out var result) ? result : null;

        public bool? FieldBoolean(string name) => FieldUInt32(name) switch
        {
            0 => false,
            1 => true,
            _ => null
        };
    }
}
