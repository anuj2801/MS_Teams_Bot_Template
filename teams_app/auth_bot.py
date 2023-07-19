# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import List
from botbuilder.core import (
    ConversationState,
    UserState,
    TurnContext,
)
# from botbuilder.dialogs import Dialog

# from .dialog_bot import DialogBot


class AuthBot():
    def __init__(
        self,
        conversation_state: ConversationState,
        user_state: UserState,
        # dialog: Dialog,
    ):
        self.conversation_state=conversation_state
        self.user_state=user_state
        
    def on_turn(self, turn_context: TurnContext):
        super().on_turn(turn_context)
        
        # Save any state changes that might have occurred during the turn.
        # await self.conversation_state.save_changes(turn_context, False)
        # await self.user_state.save_changes(turn_context, False)  
