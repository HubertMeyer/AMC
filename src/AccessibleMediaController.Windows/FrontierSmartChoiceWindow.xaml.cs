using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Threading;

namespace AccessibleMediaController.Windows;

public partial class FrontierSmartChoiceWindow : Window
{
    public FrontierSmartChoiceWindow(
        string title,
        string heading,
        IReadOnlyList<FrontierSmartChoiceRow> choices,
        uint? selectedKey = null)
    {
        InitializeComponent();
        Title = title;
        HeadingText.Text = heading;
        ChoiceList.ItemsSource = choices;
        ChoiceList.SelectedItem = choices.FirstOrDefault(choice => choice.Key == selectedKey);
        if (ChoiceList.SelectedItem is null && choices.Count > 0) ChoiceList.SelectedIndex = 0;
        Loaded += (_, _) => Dispatcher.BeginInvoke(FocusSelected, DispatcherPriority.ContextIdle);
    }

    public uint? SelectedKey { get; private set; }

    private void Choose()
    {
        if (ChoiceList.SelectedItem is not FrontierSmartChoiceRow row) return;
        if (!row.CanActivate)
        {
            StatusText.Announce($"Opcja {row.NavigationText} nie jest dostępna do bezpośredniego wyboru.");
            FocusSelected();
            return;
        }
        SelectedKey = row.Key;
        DialogResult = true;
    }

    private void Choose_Click(object sender, RoutedEventArgs e) => Choose();
    private void ChoiceList_MouseDoubleClick(object sender, MouseButtonEventArgs e) => Choose();

    private void FocusSelected()
    {
        ChoiceList.UpdateLayout();
        if (ChoiceList.ItemContainerGenerator.ContainerFromItem(ChoiceList.SelectedItem) is ListBoxItem item)
        {
            item.Focus();
            Keyboard.Focus(item);
            return;
        }
        ChoiceList.Focus();
        Keyboard.Focus(ChoiceList);
    }

    private void Window_PreviewKeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key != Key.Enter || !ChoiceList.IsKeyboardFocusWithin) return;
        Choose();
        e.Handled = true;
    }
}

public sealed record FrontierSmartChoiceRow(uint Key, string Label, string NavigationText, bool CanActivate = true)
{
    public override string ToString() => Label;
}
