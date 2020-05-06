/*******************************************************************************
 *   (c) 2016 Ledger
 *   (c) 2018 Nebulous
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 ********************************************************************************/

/*******************************************************************************
 * A high-level description of this file is as follows. The user initiates
 * the command on their computer by requesting the generation of a specific
 * public key. The command handler then displays a screen asking the user to
 * confirm the action. If the user presses the 'approve' button, the requested
 * key is generated, sent to the computer, and displayed on the device. The
 * user may then visually compare the key shown on the device to the key
 * received by the computer. Augmenting this, the user may optionally request
 * that an address be generated from the public key, in which case this
 * address is displayed instead of the public key. A final two-button press
 * returns the user to the main screen. -- This code is derived from Sia's.
 ********************************************************************************/

#include <os.h>
#include <os_io_seproxyhal.h>
#include <cx.h>
#include "crypto.h"
#include "ux.h"

// Get a pointer to the pk state variables.
static pubkey_context *ctx = &global.pk;

// Define the comparison screen. This is where the user will compare the
// public key on their device to the one shown on the computer.
static const bagl_element_t ui_pubkey_compare[] = {
  UI_BACKGROUND(),
  UI_ICON_LEFT(0x01, BAGL_GLYPH_ICON_LEFT),
  UI_ICON_RIGHT(0x02, BAGL_GLYPH_ICON_RIGHT),
  UI_TEXT(0x00, 0, 12, 128, "Compare:"),
  UI_TEXT(0x00, 0, 26, 128, global.pk.partial_str),
};

// Define the preprocessor for the comparison screen. This preprocessor
// selectively hides the left/right arrows.
static const bagl_element_t* ui_prepro_pubkey_compare(const bagl_element_t *element) {
  if ((element->component.userid == 1 && ctx->display_index == 0) ||
      (element->component.userid == 2 && ctx->display_index == affine_bytes-12)) {
    return NULL;
  }
  return element;
}

// Define the button handler for the comparison screen.
static unsigned int ui_pubkey_compare_button(unsigned int button_mask, unsigned int button_mask_counter) {
  switch (button_mask) {
  case BUTTON_LEFT:
  case BUTTON_EVT_FAST | BUTTON_LEFT: // SEEK LEFT
    if (ctx->display_index > 0) {
      ctx->display_index--;
    }
    os_memmove(ctx->partial_str, ctx->full_str+ctx->display_index, 12);
    UX_REDISPLAY();
    break;

  case BUTTON_RIGHT:
  case BUTTON_EVT_FAST | BUTTON_RIGHT: // SEEK RIGHT
    if (ctx->display_index < affine_bytes-12) {
      ctx->display_index++;
    }
    os_memmove(ctx->partial_str, ctx->full_str+ctx->display_index, 12);
    UX_REDISPLAY();
    break;

  case BUTTON_EVT_RELEASED | BUTTON_LEFT | BUTTON_RIGHT: // PROCEED
    ui_idle();
    break;
  }
  return 0;
}

void bin2hex(uint8_t *dst, uint8_t *data, size_t inlen) {
  static uint8_t const hex[] = "0123456789abcdef";
  for (size_t i = 0; i < inlen; i++) {
    dst[2*i+0] = hex[(data[i]>>4) & 0x0F];
    dst[2*i+1] = hex[(data[i]>>0) & 0x0F];
  }
  dst[2*inlen] = '\0';
}


int bin2dec(uint8_t *dst, uint64_t n) {
  if (n == 0) {
    dst[0] = '0';
    dst[1] = '\0';
    return 1;
  }
  // determine final length
  int len = 0;
  for (uint64_t nn = n; nn != 0; nn /= 10) {
    len++;
  }
  // write digits in big-endian order
  for (int i = len-1; i >= 0; i--) {
    dst[i] = (n % 10) + '0';
    n /= 10;
  }
  dst[len] = '\0';
  return len;
}

// Define the approval screen. This is where the user will approve the
// generation of the public key.
static const bagl_element_t ui_pubkey_approve[] = {
  UI_BACKGROUND(),
  UI_ICON_LEFT(0x00, BAGL_GLYPH_ICON_CROSS),
  UI_ICON_RIGHT(0x00, BAGL_GLYPH_ICON_CHECK),
  UI_TEXT(0x00, 0, 12, 128, global.pk.type_str),
  UI_TEXT(0x00, 0, 26, 128, global.pk.key_str),
};

// This is the button handler for the approval screen. If the user approves,
// it generates and sends the public key.
static unsigned int ui_pubkey_approve_button(unsigned int button_mask, unsigned int button_mask_counter) {
  // The response APDU will contain multiple objects, which means we need to
  // remember our offset within G_io_apdu_buffer. By convention, the offset
  // variable is named 'tx'.
  uint16_t tx = 0;
  affine public_key;
  scalar priv_key;
  switch (button_mask) {
  case BUTTON_EVT_RELEASED | BUTTON_LEFT: // REJECT
    io_exchange_with_code(SW_USER_REJECTED, 0);
    ui_idle();
    break;

  case BUTTON_EVT_RELEASED | BUTTON_RIGHT: // APPROVE
    // Derive the public key and address and store them in the APDU
    // buffer. Even though we know that tx starts at 0, it's best to
    // always add it explicitly; this prevents a bug if we reorder the
    // statements later.
    generate_keypair(ctx->key_index, &public_key, priv_key);
    os_memmove(G_io_apdu_buffer + tx, &public_key, affine_bytes);
    tx += affine_bytes;
    // Flush the APDU buffer, sending the response.
    io_exchange_with_code(SW_OK, tx);

    // Prepare the comparison screen, filling in the header and body text.
    os_memmove(ctx->type_str, "Compare:", 9);
    // The APDU buffer contains the raw bytes of the public key, so
    // first we need to convert to a human-readable form.
    bin2hex(ctx->full_str, G_io_apdu_buffer, field_bytes);
    os_memmove(ctx->partial_str, ctx->full_str, 12);
    ctx->partial_str[12] = '\0';
    ctx->display_index = 0;
    // Display the comparison screen.
    UX_DISPLAY(ui_pubkey_compare, ui_prepro_pubkey_compare);
    break;
  }
  return 0;
}

// handle_pubkey is the entry point for getting the public key. It
// reads the command parameters, prepares and displays the approval screen,
// and sets the IO_ASYNC_REPLY flag.
void handle_pubkey(uint8_t *data_buffer, uint16_t data_length, volatile unsigned int *flags, volatile unsigned int *tx) {

  ctx->key_index = U4LE(data_buffer, 0);
  os_memmove(ctx->type_str, "Generate Public", 16);
  os_memmove(ctx->key_str, "Key #", 5);
  int n = bin2dec(ctx->key_str + 5, ctx->key_index);
  os_memmove(ctx->key_str + 5 + n, "?", 2);
  UX_DISPLAY(ui_pubkey_approve, NULL);

  *flags |= IO_ASYNCH_REPLY;
}
