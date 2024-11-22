
# Stuff_MISIS Telegram Bot

Welcome to the **Stuff_MISIS** repository! This bot facilitates a marketplace for students and staff of MISIS University, where users can buy and sell items seamlessly. 

---

## Features

- **Buy Items**: Browse categories to find items for purchase.
- **Sell Items**: List items for sale, including details like category, name, price, contact info, and photos.
- **My Items**: View and manage the items you've listed for sale.
- **Purchased Items**: Review the items you've bought.
- **Profile**: Get a summary of your activity on the platform.
- **Help**: Access a guide for navigating the bot.

---

## Requirements

- Python 3.9 or higher
- Telegram Bot Token (set in `.env` file)

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/stuff_misis.git
   cd stuff_misis
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the project root and add your Telegram Bot token:
   ```env
   TELEGRAM_BOT_TOKEN=your-telegram-bot-token
   ```

4. **Run the bot:**
   ```bash
   python bot.py
   ```

---

## Usage

1. **Start the bot**: Use `/start` to open the main menu.
2. **Main Menu**: Navigate through the menu options using buttons for buying, selling, and managing items.
3. **Selling Items**:
   - Select a category.
   - Provide the item's name, price, contact number, and photo.
   - Confirm the item listing.
4. **Buying Items**:
   - Browse categories.
   - View items with details like price and contact information.
   - Confirm purchase to add the item to your purchased list.

---

## Directory Structure

- **Categories**: Item categories like "Бытовая техника", "Мебель", etc., are stored as folders.
- **User Data**: Each user has a `user_data_{user_id}.json` file for storing item details.
- **Photos**: Uploaded item photos are saved in their respective category folders.

---

## Bot Commands

| Command | Description                            |
|---------|----------------------------------------|
| `/start`| Opens the main menu.                  |
| `/help` | Provides a guide for using the bot.   |

---

## Key Functionalities

- **Persistent Data**: User data (e.g., items listed or purchased) is stored locally in JSON files.
- **Item Expiry**: Items are automatically removed 30 days after listing.
- **Validation**: Ensures accurate inputs for contact numbers and item details.
- **Photo Support**: Users can upload photos of items for better visibility.

---

## Future Enhancements

- Integration with a database for better scalability.
- Advanced search and filter options for buyers.
- Multi-language support beyond Russian.

---

## Contributing

Contributions are welcome! Feel free to fork the repository and submit pull requests.

---

## License

This project is licensed under the [MIT License](LICENSE). 

---

## Contact

For inquiries or issues, please reach out to the repository maintainer.