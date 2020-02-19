import logging
import json

logging.getLogger().setLevel(logging.INFO)

class filequeue:
    def __init__(self,filepath):
        self.file_path = filepath
        self.message_index = 0

    def send_message(self,MessageBody):
        filename = self.file_path.format( self.message_index )

        message = { "Records": [ {"messageId":filename,'body':MessageBody} ] }
        with open( filename, 'w') as of:
            logging.info( 'Saved message {}'.format( filename ) )
            of.write( json.dumps( message ) )

        self.message_index += 1

        return {'MessageId':filename}

